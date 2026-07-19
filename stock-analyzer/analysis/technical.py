"""テクニカル分析: 価格・出来高から売買タイミングの参考指標を計算する。"""

import pandas as pd


def _sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal, macd - signal


def _bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = close.rolling(window).mean()
    std = close.rolling(window).std()
    return mid + num_std * std, mid, mid - num_std * std


def _detect_latest_cross(short_ma: pd.Series, long_ma: pd.Series) -> dict:
    """短期MAと長期MAの直近クロス（ゴールデン/デッド）を検出する。"""
    diff = (short_ma - long_ma).dropna()
    sign = diff.apply(lambda x: 1 if x > 0 else -1)
    changes = sign.diff().dropna()
    crosses = changes[changes != 0]

    if crosses.empty:
        return {"type": None, "date": None}

    last_cross_date = crosses.index[-1]
    cross_type = "golden_cross" if changes.loc[last_cross_date] > 0 else "dead_cross"
    return {"type": cross_type, "date": str(last_cross_date.date())}


def compute_technical(history: pd.DataFrame) -> dict:
    close = history["Close"]
    volume = history["Volume"]

    ma = {w: _sma(close, w) for w in (5, 25, 75, 200)}
    rsi = _rsi(close)
    macd, signal, hist = _macd(close)
    upper, mid, lower = _bollinger_bands(close)

    latest_close = float(close.iloc[-1])
    cross = _detect_latest_cross(ma[25], ma[75])

    lookback_20 = history.tail(20)
    lookback_252 = history.tail(252)

    return {
        "latest_close": latest_close,
        "latest_date": str(close.index[-1].date()),
        "moving_averages": {f"ma{w}": (float(s.iloc[-1]) if pd.notna(s.iloc[-1]) else None) for w, s in ma.items()},
        "rsi_14": float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None,
        "macd": {
            "macd": float(macd.iloc[-1]) if pd.notna(macd.iloc[-1]) else None,
            "signal": float(signal.iloc[-1]) if pd.notna(signal.iloc[-1]) else None,
            "histogram": float(hist.iloc[-1]) if pd.notna(hist.iloc[-1]) else None,
        },
        "bollinger_bands": {
            "upper": float(upper.iloc[-1]) if pd.notna(upper.iloc[-1]) else None,
            "mid": float(mid.iloc[-1]) if pd.notna(mid.iloc[-1]) else None,
            "lower": float(lower.iloc[-1]) if pd.notna(lower.iloc[-1]) else None,
        },
        "volume": {
            "latest": int(volume.iloc[-1]),
            "avg_20d": float(lookback_20["Volume"].mean()),
        },
        "cross_signal": {
            "ma_pair": "MA25 / MA75",
            **cross,
        },
        "support_resistance": {
            "range_20d_high": float(lookback_20["High"].max()),
            "range_20d_low": float(lookback_20["Low"].min()),
            "range_52w_high": float(lookback_252["High"].max()),
            "range_52w_low": float(lookback_252["Low"].min()),
        },
    }
