import json
from datetime import datetime, timezone
import streamlit as st
from portfolio import read_portfolio, validate_portfolio, calculate
from storage import StorageError
from market import fmt, note


def load_holdings(store):
    saved = store.list('portfolio')
    if saved:
        row = next((r for r in saved if r['id'] == 'portfolio'), saved[0])
        return validate_portfolio(row['payload']), row
    return read_portfolio(), None


def quote_values(payloads):
    result = {}
    for symbol, (p, warning) in payloads.items():
        if p is None:
            continue
        raw = p['raw']
        age = (datetime.now(timezone.utc).date() - raw.index[-1].date()).days
        result[symbol] = dict(price=float(raw.iloc[-1]), previous=float(raw.iloc[-2]) if len(raw) > 1 else None,
                              date=raw.index[-1].date().isoformat(),
                              previous_date=raw.index[-2].date().isoformat() if len(raw)>1 else None,
                              daily_valid=not warning and age <= 4 and len(raw)>1)
    return result


def money(value, krw=None):
    result = '—' if value is None else '$'+fmt(value)
    if krw is not None:
        result += f' · ₩{krw:,.0f}'
    return result


def render_portfolio(holdings, payloads):
    fx_payload, fx_warning = payloads.get('KRW=X', (None, None))
    fx = float(fx_payload['raw'].iloc[-1]) if fx_payload else None
    rows, totals = calculate(holdings, quote_values(payloads), fx)
    st.title('나의 포트폴리오')
    st.caption('현재 보유 수량 기준 · USD 자산 · 평가손익(미실현)')
    for label, key, extra in [('Total Portfolio Value', 'value', None), ("Today’s P/L", 'day', totals['day_return']),
                              ('Total P/L', 'pnl', totals['return_pct'])]:
        with st.container(border=True):
            st.metric(label, '—' if totals[key] is None else '$'+fmt(totals[key]),
                      delta=fmt(extra, '%', True) if extra is not None else None)
            if totals[key+'_krw'] is not None:
                st.caption(f"약 ₩{totals[key+'_krw']:,.0f}")
    with st.container(border=True):
        st.metric('Allocation Drift', fmt(totals['drift'], ' / 100'))
        st.caption('현재·목표 비중 차이 절댓값 합계의 절반 · 정보용')
    if not any(h['shares'] for h in holdings.values()):
        st.info('아직 보유 수량을 입력하지 않았습니다. Holdings에서 수량·평단을 입력하세요. 목표 20%씩은 편집용 초기값입니다.')
    if not totals['complete']:
        st.warning(f"일부 보유 자산의 가격이 없어 총액·비중을 계산하지 않았습니다. 조회된 자산만의 소계: ${totals['subtotal']:,.2f}")
    if not totals['daily_complete']:
        st.warning('보유 자산의 당일/전일 가격이 없거나 기준 거래일이 달라 오늘 전체 손익·기여도 계산을 보류했습니다.')
    if abs(totals['target_total']-100) > 1e-6:
        st.warning(f"목표비중 합계가 {totals['target_total']:.2f}%입니다. 합계 100%일 때 Drift Score가 계산됩니다.")
    for symbol, (payload, warning) in payloads.items():
        if warning:
            st.warning(f'{symbol}: {warning}')
    if fx_payload:
        st.caption(f'환산: 1 USD = ₩{fx:,.2f} · 현재 환율 단순 환산이며 환차손익은 포함하지 않습니다.')
        note(fx_payload)
    else:
        st.caption('환율 데이터가 없어 USD만 표시합니다.')
    st.subheader('보유 자산')
    for row in rows:
        with st.container(border=True):
            st.subheader(row['ticker'])
            st.metric('현재 평가금액', '—' if row['value'] is None else '$'+fmt(row['value']),
                      delta=fmt(row['return_pct'], '%', True) if row['return_pct'] is not None else None)
            if row['value_krw'] is not None:
                st.caption(f"약 ₩{row['value_krw']:,.0f}")
            st.write(f"현재 {fmt(row['weight'], '%')} / 목표 {row['target_weight']:.2f}%")
            with st.expander('상세 데이터'):
                for label, value in [('보유 수량', fmt(row['shares'])), ('평균 매수가', '$'+fmt(row['average_price'])),
                                     ('현재 가격', money(row['price'])), ('총 투자원금', money(row['cost'], row['cost_krw'])),
                                     ('평가손익', money(row['pnl'], row['pnl_krw'])), ('평가수익률', fmt(row['return_pct'], '%', True)),
                                     ('오늘 가격 손익', money(row['day'], row['day_krw'])),
                                     ('오늘 수익률 기여도', fmt(row['contribution'], '%p', True)),
                                     ('목표 대비 차이', fmt(row['difference'], '%p', True))]:
                    st.caption(label)
                    st.write(value)
                p = payloads.get(row['ticker'], (None, None))[0]
                if p:
                    note(p)
    st.subheader('Portfolio Allocation')
    st.caption('현재 비중과 목표 비중 · 매수/매도 추천이 아닌 상태 표시')
    for r in rows:
        with st.container(border=True):
            st.write(f"**{r['ticker']}** · {r['status']}")
            st.caption(f"Current {fmt(r['weight'], '%')} · Target {r['target_weight']:.2f}% · Difference {fmt(r['difference'], '%p', True)}")
            if r['weight'] is not None:
                st.progress(min(1.0, max(0.0, r['weight']/100)), text=f"현재 {r['weight']:.2f}%")
            st.progress(r['target_weight']/100, text=f"목표 {r['target_weight']:.2f}%")
    with st.expander('포트폴리오 계산 기준'):
        st.write(f"총 투자원금: {money(totals['cost'], totals['cost_krw'])}")
        st.markdown('''- 평가금액 = 수량 × 현재 가격. 원금 = 수량 × 평균 매수가. 평가손익 = 평가금액 − 원금.
- 오늘 손익은 현재 수량 × (최신 거래일 가격 − 전 거래일 가격)입니다. 오늘 수량이 변하지 않았다고 가정한 가격 손익이며, 실제 계좌의 당일 실현손익·입출금·배당·수수료는 반영하지 않습니다.
- 오늘 수익률 = 전체 오늘 손익 / 현재 수량으로 계산한 전일 평가금액 × 100. 종목별 기여도도 같은 전체 분모를 사용하며 합계가 전체 오늘 수익률입니다.
- 원화 표시는 모두 최신 USD/KRW를 곱한 참고 환산값입니다. 매수일 환율을 반영한 실제 원화 수익률이 아닙니다.
- Drift = Σ|현재 비중 − 목표 비중| ÷ 2, 0~100. 보유금액 0·가격 누락·목표합계 100% 아님은 계산하지 않습니다.
- Balanced: 차이 절댓값 ≤2%p, Watch: 2%p 초과~5%p 이하, Large Deviation: 5%p 초과.
- 현금·채무·공매도·비USD 자산은 이 MVP에 포함하지 않습니다. 평단·수량은 주식분할 이후 기준으로 입력하세요.''')


def render_holdings(store, holdings, saved):
    st.title('Holdings')
    st.caption('수량·평단·목표비중 관리 · 실제 보유정보는 공개 GitHub 파일에 올리지 마세요.')
    if st.session_state.pop('holding_notice', None):
        st.success('보유 정보를 저장했습니다.')
    st.download_button('portfolio.json 다운로드', json.dumps(holdings, ensure_ascii=False, indent=2), 'portfolio.private.json', 'application/json')
    with st.expander('JSON 파일로 일괄 변경'):
        uploaded = st.file_uploader('portfolio.json 불러오기', type=['json'], key='portfolio_upload')
        if uploaded:
            try:
                if uploaded.size > 100_000:
                    raise ValueError('100KB 이하의 파일만 사용할 수 있습니다.')
                parsed = validate_portfolio(json.loads(uploaded.getvalue()))
                st.caption(f"{len(parsed)}종목 · 목표비중 합계 {sum(h['target_weight'] for h in parsed.values()):.2f}%")
                if st.button('파일 내용으로 전체 보유정보 저장'):
                    store.save('portfolio', parsed, 'portfolio', saved['revision'] if saved else None)
                    st.session_state.pop('holdings_edit', None)
                    st.session_state['holding_notice'] = True
                    st.rerun()
            except (ValueError, StorageError) as exc:
                st.error(str(exc))
    symbol = st.selectbox('편집할 종목', list(holdings)+['새 종목 추가'])
    if st.button('종목 편집 열기', use_container_width=True):
        st.session_state['holdings_edit'] = dict(symbol=symbol, holdings=holdings, revision=saved['revision'] if saved else None)
    snapshot = st.session_state.get('holdings_edit')
    if snapshot:
        current = snapshot['holdings'].get(snapshot['symbol'], dict(shares=0., average_price=0., target_weight=0.))
        new = snapshot['symbol'] == '새 종목 추가'
        with st.form('holding_form_'+snapshot['symbol']):
            ticker = st.text_input('Ticker', value='' if new else snapshot['symbol'], disabled=not new, max_chars=15)
            shares = st.number_input('보유 수량', min_value=0., max_value=1e12, value=current['shares'], format='%.6f')
            average = st.number_input('평균 매수가 (USD)', min_value=0., max_value=1e12, value=current['average_price'], format='%.4f')
            target = st.number_input('목표 비중 (%)', min_value=0., max_value=100., value=current['target_weight'], step=1.)
            submit = st.form_submit_button('보유정보 저장', use_container_width=True)
        if submit:
            try:
                updated = dict(snapshot['holdings'])
                ticker = ticker.strip().upper()
                if new and ticker in updated:
                    raise ValueError('이미 등록된 종목입니다. 기존 종목을 편집하세요.')
                updated[ticker] = dict(shares=shares, average_price=average, target_weight=target)
                store.save('portfolio', validate_portfolio(updated), 'portfolio', snapshot['revision'])
                st.session_state.pop('holdings_edit', None)
                st.session_state['holding_notice'] = True
                st.rerun()
            except (ValueError, StorageError) as exc:
                st.error(str(exc))
    st.caption('저장 후 Portfolio에서 확인하세요. 목표비중 합계는 100%로 맞추세요. 종목 제거는 JSON에서 해당 항목을 제거한 후 일괄 저장합니다.')
