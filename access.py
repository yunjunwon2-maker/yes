"""Guard all private reads/writes. No secret configured => isolated sandbox only."""
import hashlib
import hmac
import threading
import time
import uuid
from pathlib import Path
import streamlit as st
from storage import LocalStore, SupabaseStore, StorageError


def settings():
    try:
        return st.secrets.to_dict()
    except FileNotFoundError:
        return {}


@st.cache_resource
def attempts():
    return {'lock': threading.Lock(), 'failures': [], 'blocked_until': 0.0}


def authenticated(config):
    password = str(config.get('access', {}).get('password', ''))
    if not password or password.startswith('REPLACE_'):
        return False
    fingerprint = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(st.session_state.get('owner_auth', ''), fingerprint)


def unlock(config):
    password = str(config.get('access', {}).get('password', ''))
    if not password or password.startswith('REPLACE_'):
        if config.get('supabase'):
            st.error('외부 저장소를 사용하려면 Secrets의 [access] password를 먼저 설정하세요.')
            return False
        st.warning('임시 체험 저장 · 현재 브라우저 세션에서만 접근할 수 있습니다. 새로고침·세션 종료·재배포 시 복원이 보장되지 않습니다. 기록 후 JSON 백업을 내려받으세요.')
        return True
    if authenticated(config):
        if st.button('개인 영역 잠그기'):
            for key in list(st.session_state):
                if key != 'last_good':
                    del st.session_state[key]
            st.rerun()
        return True
    st.info('보유정보와 투자일지는 소유자 비밀번호로 보호됩니다. 시장 데이터는 Market 페이지에서 볼 수 있습니다.')
    with st.form('owner_login'):
        entered = st.text_input('소유자 비밀번호', type='password')
        submitted = st.form_submit_button('개인 영역 열기', use_container_width=True)
    if submitted:
        guard = attempts()
        now = time.monotonic()
        with guard['lock']:
            guard['failures'] = [t for t in guard['failures'] if now-t < 300]
            if now < guard['blocked_until']:
                st.error('로그인 시도가 많습니다. 5분 후 다시 시도하세요.')
            elif hmac.compare_digest(entered.encode(), password.encode()):
                guard['failures'] = []
                st.session_state['owner_auth'] = hashlib.sha256(password.encode()).hexdigest()
                st.rerun()
            else:
                guard['failures'].append(now)
                if len(guard['failures']) >= 5:
                    guard['blocked_until'] = now + 300
                st.error('비밀번호를 확인하세요.')
    return False


def get_store(config):
    remote = config.get('supabase')
    if remote:
        if not authenticated(config):
            raise StorageError('개인 영역 로그인이 필요합니다.')
        if not remote.get('url') or not remote.get('key'):
            raise StorageError('Supabase URL과 key를 모두 설정하세요.')
        return SupabaseStore(str(remote['url']), str(remote['key'])), 'Supabase · 외부 영구 저장'
    root = Path(__file__).with_name('runtime')
    if authenticated(config):
        name = 'owner'
        label = '임시 SQLite · 서버 재시작/재배포 시 소실 가능 · JSON 백업 필요'
    else:
        name = st.session_state.setdefault('sandbox_id', str(uuid.uuid4()))
        label = '세션별 임시 SQLite · 다른 기기와 동기화되지 않음'
    try:
        return LocalStore(root / (name + '.sqlite3')), label
    except Exception:
        raise StorageError('임시 저장소를 열지 못했습니다. 저장 권한을 확인하세요.') from None
