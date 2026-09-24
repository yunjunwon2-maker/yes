"""Thin router: preserve market data/metrics; compose portfolio and journal pages."""
import streamlit as st
from access import settings, unlock, get_store
from data import load, fetch_history
from portfolio import DEFAULT_SYMBOLS
from portfolio_ui import load_holdings, render_portfolio, render_holdings
from market import render_style, render_market
from details import render_details
from journal_ui import render_journal
from storage import StorageError

st.set_page_config(page_title='Pocketfolio | 투자 대시보드', page_icon='◈', layout='wide')
render_style()
st.markdown('<div class="eyebrow">POCKETFOLIO / PERSONAL INVESTING</div>', unsafe_allow_html=True)
page = st.selectbox('페이지', ['Portfolio', 'Market', 'Asset Details', 'Investment Journal', 'Holdings'])


def quotes(symbols):
    # One call per unique symbol per run. data.py shares the same 10-minute cache.
    with st.spinner('시장 데이터 조회 중…'):
        return {s: load(s) for s in dict.fromkeys(symbols)}


def refresh():
    if st.button('↻ 데이터 새로고침', use_container_width=True):
        fetch_history.clear()
    st.caption('무료 데이터 · 실시간 보장 없음 · 10분 캐시')


if page == 'Market':
    st.title('시장 대시보드')
    refresh()
    render_market(quotes([*DEFAULT_SYMBOLS, '^TNX', '^VIX', 'KRW=X']))
else:
    try:
        config = settings()
        allowed = unlock(config)
        if allowed:
            store, label = get_store(config)
            st.caption(label)
            try:
                holdings, saved = load_holdings(store)
            except (ValueError, OSError):
                st.error('portfolio.json 형식을 확인하세요. 투자일지와 시장 데이터는 계속 사용할 수 있습니다.')
                holdings, saved = {}, None
            symbols = list(dict.fromkeys([*DEFAULT_SYMBOLS, *holdings]))
            if page == 'Investment Journal':
                render_journal(store, symbols)
            elif page == 'Holdings':
                if holdings:
                    render_holdings(store, holdings, saved)
            elif page == 'Asset Details':
                ticker = st.selectbox('종목', symbols)
                refresh()
                payload, warning = quotes([ticker])[ticker]
                render_details(ticker, payload, warning, store)
            elif holdings:
                refresh()
                render_portfolio(holdings, quotes([*holdings, 'KRW=X']))
    except StorageError as exc:
        st.error(str(exc))
        st.info('시장 데이터는 Market 페이지에서 계속 확인할 수 있습니다. 외부 저장 오류 시 임시 저장소로 자동 전환하지 않습니다.')
    except Exception:
        st.error('개인 영역을 불러오지 못했습니다. 설정과 데이터 형식을 확인하세요. Market 페이지는 계속 사용할 수 있습니다.')
