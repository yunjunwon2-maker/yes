"""Transparent condition summary; the original MVP had no separate Risk Engine."""
import streamlit as st
from metrics import summarize
from market import fmt, note
from journal_ui import past_decisions


def risk_conditions(series, metrics):
    last = float(series.iloc[-1])
    checks = []
    for label, value, condition in [
        ('수정주가 < 200일 이동평균', metrics['ma200'], lambda x: last < x),
        ('RSI ≥ 70 또는 ≤ 30', metrics['rsi'], lambda x: x >= 70 or x <= 30),
        ('20일 연율 변동성 ≥ 30%', metrics['volatility'], lambda x: x >= 30),
        ('최근 1년 MDD ≤ -20%', metrics['mdd'], lambda x: x <= -20)]:
        checks.append((label, '데이터 부족' if value is None else '해당' if condition(value) else '미해당'))
    return checks


def render_details(symbol, payload, warning, store=None):
    st.title(f'{symbol} · 상세 분석')
    if warning:
        st.warning(warning)
    if payload:
        st.metric('현재 가격', '$'+fmt(float(payload['raw'].iloc[-1])))
        note(payload)
        s = payload['adjusted']
        if not s.empty and s.index[-1] == payload['raw'].index[-1]:
            m = summarize(s)
            chart = s.rename('수정주가').to_frame()
            for n in (20, 60, 200):
                chart[f'MA {n}'] = s.rolling(n).mean()
            st.line_chart(chart.tail(252), height=300)
            with st.expander('수익률과 기술지표', expanded=True):
                for label, key, unit in [('오늘', 'day', '%'), ('1주', 'week', '%'), ('1개월', 'month', '%'), ('RSI(14)', 'rsi', ''),
                                         ('20일 이동평균', 'ma20', ' USD'), ('60일 이동평균', 'ma60', ' USD'), ('200일 이동평균', 'ma200', ' USD'),
                                         ('변동성', 'volatility', '%'), ('MDD', 'mdd', '%')]:
                    st.write(f'{label}: {fmt(m[key], unit)}')
            with st.expander('Risk Engine · 지표 상태', expanded=True):
                for label, status in risk_conditions(s, m):
                    st.write(f'{label}: **{status}**')
                st.caption('명시된 기준의 충족 여부만 표시합니다. 매수·매도 추천이나 향후 손실 예측이 아닙니다. RSI 극단값은 단기 국채 ETF에서도 발생할 수 있습니다.')
        else:
            st.warning('수정주가가 없어 차트·기술지표 계산을 보류했습니다.')
    else:
        st.info('가격 데이터가 없습니다. 일지는 아래에서 확인할 수 있습니다.')
    if store is not None:
        past_decisions(store, symbol)
