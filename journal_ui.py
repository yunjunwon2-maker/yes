import json
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo
import streamlit as st
from storage import ACTIONS, FIELDS, StorageError, validate_entry, filter_entries

LABELS = dict(reasoning='당시 판단', thesis='투자 논리', risk='리스크 요인', check_again='향후 확인할 조건', notes='메모')


def entry_form(key, symbols, initial=None):
    p = initial or {}
    tickers = sorted(set(symbols) | {p.get('ticker', 'PORTFOLIO'), 'PORTFOLIO'})
    with st.form(key, clear_on_submit=False):
        day = st.date_input('날짜', value=date.fromisoformat(p['date']) if p.get('date') else datetime.now(ZoneInfo('Asia/Seoul')).date())
        ticker = st.selectbox('관련 종목', tickers, index=tickers.index(p.get('ticker', tickers[0])))
        action = st.selectbox('행동', ACTIONS, index=ACTIONS.index(p.get('action', 'Hold')))
        title = st.text_input('제목', value=p.get('title', ''), max_chars=160)
        values = {k: st.text_area(label, value=p.get(k, ''), height=100, max_chars=10000) for k, label in LABELS.items()}
        submitted = st.form_submit_button('저장', use_container_width=True)
    return submitted, dict(date=day.isoformat(), ticker=ticker, action=action, title=title, **values)


def show_record(r, prefix='past'):
    p = r['payload']
    with st.expander(f"{p['date']} · {p['ticker']} · {p['action']} — {p['title']}"):
        for k, label in LABELS.items():
            st.caption(label)
            st.text(p.get(k) or '—')
        st.caption(f"수정 시각(UTC): {r['updated_at']} · 버전 {r['revision']}")


def past_decisions(store, ticker):
    st.subheader('Past Decisions')
    try:
        rows = filter_entries(store.list('journal'), ticker=ticker)
        if not rows:
            st.caption('이 종목의 투자일지가 아직 없습니다.')
        for row in rows[:20]:
            show_record(row)
        if len(rows) > 20:
            st.caption('최근 20건입니다. 전체 기록은 Investment Journal에서 확인하세요.')
    except StorageError as exc:
        st.warning(str(exc))


def render_journal(store, symbols):
    st.title('Investment Journal')
    st.caption('판단을 기록하고, 시간이 지난 뒤 다시 살펴보세요. 일지 입력은 보유 수량을 자동 변경하지 않습니다.')
    if st.session_state.pop('journal_notice', None):
        st.success('변경 사항을 저장했습니다.')
    try:
        records = store.list('journal')
    except StorageError as exc:
        st.error(str(exc))
        return
    with st.expander('새 투자일지 작성', expanded=not records):
        new_id = st.session_state.setdefault('journal_new_id', str(uuid.uuid4()))
        submitted, draft = entry_form('new_'+new_id, symbols)
        if submitted:
            try:
                store.save('journal', validate_entry(draft), identifier=new_id)
                st.session_state.pop('journal_new_id', None)
                st.session_state['journal_notice'] = True
                st.rerun()
            except (ValueError, StorageError) as exc:
                st.error(str(exc))
        st.download_button('작성 중 내용 백업', json.dumps(draft, ensure_ascii=False, indent=2), 'journal-draft.json', 'application/json')
    st.subheader('기록 검색')
    with st.expander('필터', expanded=True):
        start = st.date_input('시작일', value=None, key='journal_start')
        end = st.date_input('종료일', value=None, key='journal_end')
        options = ['전체'] + sorted(set(symbols) | {r['payload']['ticker'] for r in records})
        ticker = st.selectbox('종목 필터', options)
        action = st.selectbox('행동 필터', ['전체'] + list(ACTIONS))
        keyword = st.text_input('키워드', placeholder='제목·판단·투자 논리·리스크 검색')
    if start and end and start > end:
        st.warning('시작일은 종료일보다 늦을 수 없습니다.')
        found = []
    else:
        found = filter_entries(records, start, end, None if ticker == '전체' else ticker,
                               None if action == '전체' else action, keyword)
    st.caption(f'{len(found)}건 / 전체 {len(records)}건')
    # Limit rendering only; filtering/export always includes every record.
    page = st.number_input('목록 페이지', min_value=1, max_value=max(1, (len(found)+19)//20), value=1, step=1)
    for r in found[(page-1)*20:page*20]:
        show_record(r)
        if st.button('수정 / 삭제', key='edit_'+r['id'], use_container_width=True):
            st.session_state['journal_edit'] = r
            st.rerun()
    editing = st.session_state.get('journal_edit')
    if editing:
        st.subheader('기록 수정')
        if st.button('수정 취소'):
            st.session_state.pop('journal_edit', None)
            st.rerun()
        submitted, changed = entry_form('edit_form_'+editing['id']+'_'+str(editing['revision']), symbols, editing['payload'])
        if submitted:
            try:
                store.save('journal', validate_entry(changed), editing['id'], editing['revision'])
                st.session_state.pop('journal_edit', None)
                st.session_state['journal_notice'] = True
                st.rerun()
            except (ValueError, StorageError) as exc:
                st.error(str(exc))
        confirm = st.checkbox('이 기록을 삭제하겠습니다.', key='delete_check_'+editing['id'])
        if st.button('기록 삭제', disabled=not confirm):
            try:
                store.delete(editing['id'], editing['revision'])
                st.session_state.pop('journal_edit', None)
                st.session_state['journal_notice'] = True
                st.rerun()
            except StorageError as exc:
                st.error(str(exc))
    with st.expander('전체 백업 / 복원'):
        backup = dict(schema_version=1, journal=records)
        st.download_button('투자일지 JSON 백업', json.dumps(backup, ensure_ascii=False, indent=2),
                           'journal-backup.json', 'application/json', use_container_width=True)
        st.caption('백업은 개인 파일입니다. GitHub에 올리지 마세요. 복원 시 같은 ID는 건너뛰며 기존 기록을 덮어쓰지 않습니다.')
        upload = st.file_uploader('투자일지 백업 불러오기', type=['json'])
        if upload is not None and st.button('백업 기록 복원'):
            try:
                if upload.size > 5_000_000:
                    raise ValueError('5MB 이하의 백업을 사용하세요.')
                raw = json.loads(upload.getvalue())
                if raw.get('schema_version') != 1 or not isinstance(raw.get('journal'), list):
                    raise ValueError('지원하는 투자일지 백업 형식이 아닙니다.')
                # Validate the entire import before the first write.
                valid = [(str(uuid.UUID(r['id'])), validate_entry(r['payload'])) for r in raw['journal']]
                existing = {r['id'] for r in records}
                saved = 0
                for identifier, p in valid:
                    if identifier not in existing:
                        store.save('journal', p, identifier)
                        existing.add(identifier)
                        saved += 1
                st.success(f'{saved}건 복원했습니다. 목록 갱신을 눌러 확인하세요.')
            except (ValueError, KeyError, TypeError, StorageError) as exc:
                st.error(f'복원 실패: {exc}. 일부가 이미 저장됐을 수 있습니다. 재조회하면 확인할 수 있습니다.')
        if st.button('목록 갱신'):
            st.rerun()
