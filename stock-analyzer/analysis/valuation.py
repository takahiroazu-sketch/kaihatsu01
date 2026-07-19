"""バリュエーション分析: 現在の株価が割安か割高かを見る指標を計算する。

同業他社比較は業界データソースが未整備のため v1 では対象外（企画書 今後の拡張余地を参照）。
"""

import pandas as pd


def _dividend_growth_rate(dividends: pd.Series) -> float | None:
    """直近5年の年間配当合計から、配当の年平均成長率(CAGR)を概算する。"""
    if dividends.empty:
        return None

    div = dividends.copy()
    div.index = pd.to_datetime(div.index).tz_localize(None)
    annual = div.groupby(div.index.year).sum()
    annual = annual[annual.index < annual.index.max() + 1].tail(6)  # 直近6年分（当年含む可能性があるため）

    if len(annual) < 2 or annual.iloc[0] <= 0:
        return None

    years = len(annual) - 1
    cagr = (annual.iloc[-1] / annual.iloc[0]) ** (1 / years) - 1
    return float(cagr)


def _dividend_discount_price(current_dividend_yield: float | None, latest_close: float | None,
                              dividends: pd.Series, required_return: float = 0.07) -> dict:
    """簡易配当割引モデル（ゴードン成長モデル）による理論株価。

    P = D1 / (r - g)
    r: 要求利回り（デフォルト7%、日本株の一般的な期待リターンの目安）
    g: 配当成長率（直近実績から概算）。ゴードン成長モデルは「その成長率が永久に続く」前提のため、
       実績CAGRをそのまま使うと r に近づくほど理論株価が発散して非現実的な値になる。
       そのため長期的に持続可能な成長率の目安（日本の名目GDP成長率程度）を上限としてクリップする。
    """
    LONG_TERM_GROWTH_CAP = 0.03

    if latest_close is None or current_dividend_yield is None:
        return {"theoretical_price": None, "assumptions": None}

    d0 = current_dividend_yield * latest_close
    g = _dividend_growth_rate(dividends)
    if g is None:
        g = 0.0
    g = min(g, LONG_TERM_GROWTH_CAP, required_return - 0.02)

    d1 = d0 * (1 + g)
    theoretical_price = d1 / (required_return - g) if (required_return - g) > 0 else None

    return {
        "theoretical_price": theoretical_price,
        "assumptions": {
            "required_return": required_return,
            "dividend_growth_rate": g,
            "base_dividend_per_share": d0,
        },
    }


def compute_valuation(info: dict, history: pd.DataFrame, dividends: pd.Series) -> dict:
    latest_close = float(history["Close"].iloc[-1]) if not history.empty else None

    # yfinance の dividendYield は「3.54」のようにパーセント表記そのものが入っているため、
    # 他の比率（ROEなど）と同じ小数表記(0.0354)に揃える。
    raw_yield = info.get("dividendYield")
    dividend_yield = raw_yield / 100 if raw_yield is not None else None

    ddm = _dividend_discount_price(dividend_yield, latest_close, dividends)

    return {
        "latest_close": latest_close,
        "trailing_per": info.get("trailingPE"),
        "forward_per": info.get("forwardPE"),
        "pbr": info.get("priceToBook"),
        "psr": info.get("priceToSalesTrailing12Months"),
        "ev_to_ebitda": info.get("enterpriseToEbitda"),
        "dividend_yield": dividend_yield,
        "peg_ratio": info.get("trailingPegRatio") or info.get("pegRatio"),
        "theoretical_price_ddm": ddm["theoretical_price"],
        "ddm_assumptions": ddm["assumptions"],
        "peer_comparison": None,  # v2以降: 業界平均・同業他社データソース確保後に対応
    }
