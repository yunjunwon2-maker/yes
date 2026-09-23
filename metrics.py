"""Pure daily-series calculations; no network or Streamlit dependency."""
import numpy as np
import pandas as pd


def clean(series):
    series = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    series = series.dropna().sort_index()
    return series[~series.index.duplicated(keep="last")].loc[lambda s: s > 0]


def rsi_wilder(series, period=14):
    values = clean(series).to_numpy(dtype=float)
    if len(values) <= period:
        return None
    delta = np.diff(values)
    gains, losses = np.maximum(delta, 0), np.maximum(-delta, 0)
    gain, loss = gains[:period].mean(), losses[:period].mean()
    for up, down in zip(gains[period:], losses[period:]):
        gain = (gain * (period - 1) + up) / period
        loss = (loss * (period - 1) + down) / period
    if loss == 0:
        return 50.0 if gain == 0 else 100.0
    return float(100 - 100 / (1 + gain / loss))


def summarize(series):
    s = clean(series)
    if s.empty:
        raise ValueError("유효한 가격이 없습니다.")
    def change(n):
        return float((s.iloc[-1] / s.iloc[-n - 1] - 1) * 100) if len(s) > n else None
    def ma(n):
        return float(s.tail(n).mean()) if len(s) >= n else None
    recent = s.loc[s.index >= s.index[-1] - pd.DateOffset(years=1)]
    returns = s.pct_change(fill_method=None).dropna().tail(20)
    return dict(day=change(1), week=change(5), month=change(21),
                rsi=rsi_wilder(s), ma20=ma(20), ma60=ma(60), ma200=ma(200),
                volatility=float(returns.std(ddof=1) * np.sqrt(252) * 100) if len(returns) == 20 else None,
                mdd=float((recent / recent.cummax() - 1).min() * 100) if len(recent) >= 2 else None)
