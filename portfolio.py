"""Snapshot accounting in USD. Never silently reweight incomplete quotes."""
import json
import math
import re
from pathlib import Path

DEFAULT_SYMBOLS = ("GOOGL", "NEE", "SPY", "SCHD", "SGOV")
FILE = Path(__file__).with_name("portfolio.json")


def validate_portfolio(value):
    if not isinstance(value, dict) or not 1 <= len(value) <= 50:
        raise ValueError("종목 1~50개의 JSON 객체가 필요합니다.")
    result = {}
    for ticker, holding in value.items():
        if not isinstance(ticker, str) or not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,14}", ticker):
            raise ValueError("Ticker는 대문자 영문·숫자·점·하이픈으로 입력하세요.")
        if not isinstance(holding, dict):
            raise ValueError(f"{ticker}: 보유 정보 형식이 올바르지 않습니다.")
        item = {}
        for key in ("shares", "average_price", "target_weight"):
            number = holding.get(key)
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or number < 0:
                raise ValueError(f"{ticker}: {key}는 0 이상의 유한한 숫자여야 합니다.")
            item[key] = float(number)
        if item['target_weight'] > 100 or item['shares'] > 1e12 or item['average_price'] > 1e12:
            raise ValueError(f"{ticker}: 입력값 범위를 확인하세요.")
        if item['shares'] > 0 and item['average_price'] <= 0:
            raise ValueError(f"{ticker}: 보유 수량이 있으면 평균 매수가는 0보다 커야 합니다.")
        result[ticker] = item
    return result


def read_portfolio(path=FILE):
    return validate_portfolio(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def allocation_status(difference):
    if difference is None:
        return "Unavailable"
    d = abs(difference)
    return "Balanced" if d <= 2 + 1e-9 else "Watch" if d <= 5 + 1e-9 else "Large Deviation"


def calculate(holdings, quotes, fx=None):
    """quotes[ticker]: price, previous, date, previous_date, daily_valid.

    Drift = 0.5 * sum(abs(current_weight - target_weight)) in percentage
    points. With normalized long-only weights it ranges 0..100 and measures
    the allocation gap; it is not a forecast or trade recommendation.
    Daily contribution = shares*(price-previous)/total_previous_value*100.
    Current shares are assumed unchanged since yesterday; no cash-flow ledger.
    """
    holdings = validate_portfolio(holdings)
    rows = []
    for ticker, item in holdings.items():
        q = quotes.get(ticker) or {}
        price, previous = q.get('price'), q.get('previous')
        if price is not None and (not math.isfinite(price) or price <= 0):
            price = None
        if previous is not None and (not math.isfinite(previous) or previous <= 0):
            previous = None
        shares = item['shares']
        cost = shares * item['average_price']
        value = 0.0 if shares == 0 else shares * price if price is not None else None
        pnl = value - cost if value is not None else None
        daily_ok = q.get('daily_valid', False) and price is not None and previous is not None
        day = 0.0 if shares == 0 else shares * (price - previous) if daily_ok else None
        rows.append(dict(ticker=ticker, **item, price=price, value=value, cost=cost, pnl=pnl,
                         return_pct=100*pnl/cost if cost > 0 and pnl is not None else None,
                         day=day, previous_value=shares*previous if daily_ok else 0 if shares == 0 else None,
                         date=q.get('date'), previous_date=q.get('previous_date')))
    cost = sum(r['cost'] for r in rows)
    complete = all(r['value'] is not None for r in rows)
    value = sum(r['value'] for r in rows) if complete else None
    pnl = value - cost if complete else None
    active = [r for r in rows if r['shares'] > 0]
    same_dates = len({(r['date'], r['previous_date']) for r in active}) <= 1
    daily_complete = same_dates and all(r['day'] is not None for r in active)
    day = sum(r['day'] for r in rows) if daily_complete else None
    prev = sum(r['previous_value'] for r in rows) if daily_complete else None
    target_total = sum(r['target_weight'] for r in rows)
    target_valid = abs(target_total - 100) <= 1e-6
    for r in rows:
        r['weight'] = r['value'] / value * 100 if complete and value > 0 else None
        r['difference'] = r['weight'] - r['target_weight'] if r['weight'] is not None else None
        r['status'] = allocation_status(r['difference'])
        r['contribution'] = r['day'] / prev * 100 if daily_complete and prev > 0 else None
    drift = sum(abs(r['difference']) for r in rows)/2 if complete and value > 0 and target_valid else None
    fx = fx if fx is not None and math.isfinite(fx) and fx > 0 else None
    for r in rows:
        for key in ('value', 'cost', 'pnl', 'day'):
            r[key+'_krw'] = r[key]*fx if fx is not None and r[key] is not None else None
    totals = dict(value=value, cost=cost, pnl=pnl, day=day, drift=drift,
                  return_pct=pnl/cost*100 if pnl is not None and cost > 0 else None,
                  day_return=day/prev*100 if day is not None and prev > 0 else None,
                  target_total=target_total, complete=complete, daily_complete=daily_complete,
                  subtotal=sum(r['value'] for r in rows if r['value'] is not None))
    for key in ('value', 'cost', 'pnl', 'day'):
        totals[key+'_krw'] = totals[key]*fx if fx is not None and totals[key] is not None else None
    return rows, totals
