from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo
import streamlit as st
from data import load, fetch_history
from metrics import summarize

st.set_page_config(page_title="Pocketfolio | 투자 대시보드", page_icon="◈", layout="wide")
st.markdown('''<style>
.block-container{max-width:1120px;padding-top:4.5rem;padding-bottom:3rem}
.eyebrow{color:#66e3c4;letter-spacing:.18em;font-size:.75rem;font-weight:700}
.asset{background:#151d30;border:1px solid #2a3650;border-radius:18px;padding:22px;margin:12px 0 22px;color:#e8edf5}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px}.ticker{font-size:1.3rem;font-weight:750}
.muted{color:#aab7cd;font-size:.8rem}.price{font-size:2.1rem;font-weight:750;margin:10px 0}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px 10px}
.label{color:#aab7cd;font-size:.76rem;margin-bottom:4px}.value{font-size:1.05rem;font-weight:650}
.up{color:#66e3c4}.down{color:#ff8c9b}.neutral{color:#e8edf5}.line{border-top:1px solid #2a3650;margin:18px 0}
@media(max-width:600px){.block-container{padding:4rem 1rem 2rem}.asset{padding:18px}.price{font-size:1.9rem}.grid{gap:16px 7px}.value{font-size:.95rem}h1{font-size:1.9rem!important}}
</style>''', unsafe_allow_html=True)

def fmt(value, suffix="", signed=False):
    return "—" if value is None else f"{value:+,.2f}{suffix}" if signed else f"{value:,.2f}{suffix}"

def cell(label, value, suffix="", signed=False):
    color = "neutral" if value is None or not signed or value == 0 else "up" if value > 0 else "down"
    return f'<div><div class="label">{escape(label)}</div><div class="value {color}">{fmt(value,suffix,signed)}</div></div>'

def note(payload):
    date = payload["raw"].index[-1]
    st.caption(f"가격 기준: {date:%Y-%m-%d} (거래소 일봉) · 조회: {payload['fetched'].astimezone(ZoneInfo('Asia/Seoul')):%m/%d %H:%M} KST")
    if (datetime.now(timezone.utc).date() - date.date()).days > 4:
        st.warning("최신 가격 기준일이 4일 이상 지났습니다. 휴장 또는 데이터 지연 여부를 확인하세요.")

st.markdown('<div class="eyebrow">POCKETFOLIO / MARKET WATCH</div>', unsafe_allow_html=True)
st.title("나의 투자 대시보드")
st.caption("5개 자산과 시장의 흐름을 한눈에 · USD 기준")
if st.button("↻ 데이터 새로고침", use_container_width=True):
    fetch_history.clear()
st.caption("무료 제공 데이터 · 실시간 보장 없음 · 10분 캐시 · 새로고침 또는 페이지 재접속 시 조회")

st.subheader("시장 온도")
for symbol, name, unit in [("^TNX", "미국 10년물 국채금리", "%"), ("^VIX", "VIX", ""), ("KRW=X", "USD/KRW · 1달러", "원")]:
    with st.container(border=True):
        with st.spinner(f"{name} 조회 중…"):
            payload, warning = load(symbol)
        if warning:
            st.warning(f"{name}: {warning}")
        if payload:
            st.metric(name, fmt(float(payload["raw"].iloc[-1]), unit))
            note(payload)
        else:
            st.metric(name, "—")

st.subheader("관심 자산")
st.caption("오늘 = 최신 거래일 대비 전 거래일 · 1주 = 5거래일 · 1개월 = 21거래일")
for symbol, name in [("GOOGL", "Alphabet"), ("NEE", "NextEra Energy"), ("SPY", "S&P 500 ETF"), ("SCHD", "미국 배당주 ETF"), ("SGOV", "미국 초단기 국채 ETF")]:
    with st.spinner(f"{symbol} 조회 중…"):
        payload, warning = load(symbol)
    if warning:
        st.warning(f"{symbol}: {warning}")
    if payload is None:
        st.markdown(f'<div class="asset"><div class="ticker">{symbol}</div><div class="price">—</div><div class="muted">데이터 대기 중</div></div>', unsafe_allow_html=True)
        continue
    try:
        adjusted = payload["adjusted"]
        if adjusted.empty or adjusted.index[-1] != payload["raw"].index[-1]:
            raise ValueError("수정주가가 누락되어 지표 계산을 보류합니다.")
        m = summarize(adjusted)
        rows = ''.join([cell("오늘 수익률", m['day'], '%', True), cell("1주 수익률", m['week'], '%', True), cell("1개월 수익률", m['month'], '%', True)])
        technical = ''.join([cell("RSI (14)", m['rsi']), cell("변동성 · 20일 연율", m['volatility'], '%'), cell("MDD · 최근 1년", m['mdd'], '%'), cell("20일 이동평균", m['ma20'], ' USD'), cell("60일 이동평균", m['ma60'], ' USD'), cell("200일 이동평균", m['ma200'], ' USD')])
        st.markdown(f'<div class="asset"><div class="top"><span class="ticker">{symbol}</span><span class="muted">{name}</span></div><div class="price">${payload["raw"].iloc[-1]:,.2f}</div><div class="muted">현재 가격 · 최신 일봉의 종가/장중 제공값</div><div class="line"></div><div class="grid">{rows}</div><div class="line"></div><div class="grid">{technical}</div></div>', unsafe_allow_html=True)
        note(payload)
    except Exception:
        st.metric(f"{symbol} · 현재 가격", f'${payload["raw"].iloc[-1]:,.2f}')
        st.warning(f"{symbol}: 지표 계산에 필요한 데이터가 부족하거나 형식이 잘못되었습니다.")
        note(payload)

with st.expander("지표 계산 기준과 데이터 안내"):
    st.markdown('''- **현재 가격**: Yahoo Finance 최신 일봉 Close. 장중에는 변할 수 있고 장 마감 후에는 종가입니다. 실시간 체결가가 아닙니다.
- **수익률·기술지표**: 배당·분할을 반영한 수정주가(Adj Close)로 계산합니다. 오늘은 미국 최신 거래일 기준이며 한국 날짜와 다를 수 있습니다.
- **RSI(14)**: 첫 14개 변동의 평균으로 시작하는 Wilder 평활 방식. 횡보는 50, 상승만 있으면 100입니다.
- **이동평균**: 수정주가의 최근 20/60/200거래일 단순평균. 현재 가격과 조정 기준이 다를 수 있습니다.
- **변동성**: 최근 20개 일간 단순수익률의 표본표준편차 × √252, 연율 환산.
- **MDD**: 최신 일봉 기준 최근 1년 내 수정주가의 고점 대비 최대 하락률(음수). 상장 이후 전체 MDD가 아닙니다.
- **거시 지표**: ^TNX(10년 금리, %), ^VIX, KRW=X(1 USD당 KRW). 각 기준일은 서로 다를 수 있습니다.
- 제공처 오류는 종목별로 처리합니다. 같은 세션에서 이전 조회가 성공했다면 이전값을 표시하고 경고합니다. 첫 조회 실패 시 ‘—’를 표시합니다.
- 개인 참고용이며 투자 권유가 아닙니다. 데이터는 지연·누락·정정될 수 있습니다.''')
