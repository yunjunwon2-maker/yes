"""Individual requests isolate provider failures; successful results cached 10 minutes."""
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import yfinance as yf
from metrics import clean


@st.cache_data(ttl=600, show_spinner=False, max_entries=32)
def fetch_history(symbol):
    frame = yf.Ticker(symbol).history(period="2y", interval="1d", auto_adjust=False,
                                      actions=False, timeout=12, raise_errors=True)
    if frame is None or frame.empty or "Close" not in frame:
        raise ValueError("데이터 제공처에서 가격을 받지 못했습니다.")
    raw = clean(frame["Close"])
    adjusted = clean(frame["Adj Close"]) if "Adj Close" in frame else pd.Series(dtype=float)
    if raw.empty:
        raise ValueError("유효한 가격이 없습니다.")
    return {"raw": raw, "adjusted": adjusted, "fetched": datetime.now(timezone.utc)}


def load(symbol):
    fallback = st.session_state.setdefault("last_good", {})
    try:
        result = fetch_history(symbol)
        fallback[symbol] = result
        return result, None
    except Exception:
        if symbol in fallback:
            return fallback[symbol], "갱신 실패 · 이 브라우저 세션의 이전 데이터를 표시합니다."
        return None, "데이터를 불러오지 못했습니다. 잠시 후 새로고침해 주세요."
