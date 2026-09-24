"""One-user document storage. No credentials or private records in git.

Supabase errors never silently switch to local storage. Optimistic revisions
prevent an older phone tab from overwriting a newer desktop edit.
"""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests

ACTIONS = ('Buy', 'Sell', 'Hold', 'Watch', 'Rebalance', 'Other')
FIELDS = ('reasoning', 'thesis', 'risk', 'check_again', 'notes')


class StorageError(Exception):
    pass


class ConflictError(StorageError):
    pass


def validate_entry(entry):
    try:
        d = date.fromisoformat(str(entry['date']))
    except (KeyError, ValueError):
        raise ValueError('날짜를 YYYY-MM-DD 형식으로 입력하세요.') from None
    action = entry.get('action')
    if action not in ACTIONS:
        raise ValueError('행동을 선택하세요.')
    title = str(entry.get('title', '')).strip()
    ticker = str(entry.get('ticker', '')).strip().upper()
    if not title or len(title) > 160 or not ticker or len(ticker) > 15:
        raise ValueError('제목(1~160자)과 종목을 입력하세요.')
    result = dict(date=d.isoformat(), ticker=ticker, action=action, title=title)
    for key in FIELDS:
        value = str(entry.get(key, '')).strip()
        if len(value) > 10000:
            raise ValueError('각 내용은 10,000자 이하로 입력하세요.')
        result[key] = value
    return result


def filter_entries(records, start=None, end=None, ticker=None, action=None, keyword=''):
    query = keyword.casefold().strip()
    result = []
    for r in records:
        p = r['payload']
        if start and p['date'] < str(start):
            continue
        if end and p['date'] > str(end):
            continue
        if ticker and p['ticker'] != ticker:
            continue
        if action and p['action'] != action:
            continue
        if query and query not in ' '.join(str(v) for v in p.values()).casefold():
            continue
        result.append(r)
    return sorted(result, key=lambda r: (r['payload']['date'], r['updated_at']), reverse=True)


def record(kind, payload, identifier=None, revision=1):
    return dict(id=identifier or str(uuid.uuid4()), kind=kind, payload=payload,
                revision=revision, updated_at=datetime.now(timezone.utc).isoformat(), deleted=False)


class LocalStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, revision INTEGER NOT NULL, updated_at TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0)')

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=10)
        try:
            with con:
                yield con
        finally:
            con.close()

    def list(self, kind):
        try:
            with self.connect() as con:
                con.row_factory = sqlite3.Row
                rows = con.execute('SELECT * FROM documents WHERE kind=? AND deleted=0 ORDER BY updated_at DESC', (kind,)).fetchall()
            return [dict(r, payload=json.loads(r['payload'])) for r in rows]
        except (sqlite3.Error, ValueError):
            raise StorageError('임시 저장소를 읽지 못했습니다. 백업 파일을 확인하세요.') from None

    def save(self, kind, payload, identifier=None, expected=None):
        r = record(kind, payload, identifier, (expected or 0)+1)
        try:
            with self.connect() as con:
                if expected is None:
                    con.execute('INSERT INTO documents VALUES (?,?,?,?,?,0)', (r['id'], kind, json.dumps(payload, ensure_ascii=False), r['revision'], r['updated_at']))
                else:
                    cur = con.execute('UPDATE documents SET payload=?, revision=?, updated_at=?, deleted=0 WHERE id=? AND kind=? AND revision=? AND deleted=0',
                                      (json.dumps(payload, ensure_ascii=False), r['revision'], r['updated_at'], r['id'], kind, expected))
                    if cur.rowcount != 1:
                        raise ConflictError('다른 화면에서 변경된 기록입니다. 다시 조회한 뒤 수정하세요.')
            return r
        except sqlite3.IntegrityError:
            raise ConflictError('이미 존재하는 기록입니다. 다시 조회하세요.') from None
        except sqlite3.Error:
            raise StorageError('저장하지 못했습니다. 입력 내용을 백업하고 다시 시도하세요.') from None

    def delete(self, identifier, expected):
        # Soft deletion retains a recoverable server record; UI excludes tombstones.
        try:
            with self.connect() as con:
                cur = con.execute('UPDATE documents SET deleted=1, revision=revision+1, updated_at=? WHERE id=? AND revision=? AND deleted=0',
                                  (datetime.now(timezone.utc).isoformat(), identifier, expected))
                if cur.rowcount != 1:
                    raise ConflictError('기록이 변경되었습니다. 다시 조회하세요.')
        except sqlite3.Error:
            raise StorageError('삭제 상태를 저장하지 못했습니다.') from None


class SupabaseStore:
    def __init__(self, url, key):
        parsed = urlparse(url)
        if parsed.scheme != 'https' or not parsed.hostname or not parsed.hostname.endswith('.supabase.co') or parsed.path not in ('', '/'):
            raise StorageError('Supabase Project URL을 확인하세요.')
        self.url = url.rstrip('/') + '/rest/v1/pocketfolio_documents'
        self.headers = {'apikey': key, 'Content-Type': 'application/json', 'Prefer': 'return=representation'}
        # New sb_secret keys use apikey only. Legacy JWT service_role keys also use Bearer.
        if not key.startswith('sb_secret_'):
            self.headers['Authorization'] = 'Bearer ' + key

    def request(self, method, params=None, body=None):
        try:
            res = requests.request(method, self.url, headers=self.headers, params=params, json=body, timeout=(5, 15), allow_redirects=False)
            if res.status_code == 409:
                raise ConflictError('동일 기록이 이미 있습니다. 다시 조회하세요.')
            if not 200 <= res.status_code < 300:
                raise StorageError('외부 저장소 요청 실패. Secrets·테이블·연결 상태를 확인하세요. 로컬에 대신 저장하지 않았습니다.')
            return res.json() if res.content else []
        except (requests.RequestException, ValueError):
            raise StorageError('외부 저장소 응답을 확인하지 못했습니다. 재조회 후 저장 여부를 확인하세요.') from None

    def list(self, kind):
        rows, offset = [], 0
        while True:
            batch = self.request('GET', dict(kind='eq.'+kind, deleted='eq.false', select='*', order='updated_at.desc,id.asc', limit=500, offset=offset))
            if not isinstance(batch, list):
                raise StorageError('외부 저장소 응답 형식이 올바르지 않습니다.')
            rows.extend(batch)
            if len(batch) < 500:
                return rows
            offset += 500

    def save(self, kind, payload, identifier=None, expected=None):
        r = record(kind, payload, identifier, (expected or 0)+1)
        if expected is None:
            result = self.request('POST', body=r)
        else:
            result = self.request('PATCH', dict(id='eq.'+r['id'], kind='eq.'+kind, revision='eq.'+str(expected), deleted='eq.false'), r)
        if not result:
            raise ConflictError('기록이 변경되었습니다. 다시 조회 후 수정하세요.')
        return result[0]

    def delete(self, identifier, expected):
        result = self.request('PATCH', dict(id='eq.'+identifier, revision='eq.'+str(expected), deleted='eq.false'),
                              dict(deleted=True, revision=expected+1, updated_at=datetime.now(timezone.utc).isoformat()))
        if not result:
            raise ConflictError('기록이 변경되었습니다. 다시 조회하세요.')
