"""ファンダメンタルズ分析: 損益計算書・貸借対照表・キャッシュフロー・配当から期別指標を計算する。"""

import pandas as pd


def _row(df: pd.DataFrame, label: str) -> pd.Series:
    """指定行を取り出す。存在しなければ全期間NaNのSeriesを返す。"""
    if label in df.index:
        return df.loc[label]
    return pd.Series(index=df.columns, dtype=float)


def _fiscal_year_label(period_end) -> str:
    ts = pd.Timestamp(period_end)
    return f"{ts.year}-{ts.month:02d}"


def _dividend_per_share_by_period(dividends: pd.Series, periods) -> dict:
    """配当（実績の支払日ベース）を、各決算期末（3月末想定）までの直近1年間で合算する。"""
    result = {}
    if dividends.empty:
        return {p: None for p in periods}

    div = dividends.copy()
    div.index = pd.to_datetime(div.index).tz_localize(None)

    for period in periods:
        period_end = pd.Timestamp(period).tz_localize(None)
        period_start = period_end - pd.DateOffset(years=1)
        mask = (div.index > period_start) & (div.index <= period_end)
        total = div[mask].sum()
        result[period] = float(total) if total else None
    return result


def compute_fundamentals(income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame,
                          cashflow: pd.DataFrame, dividends: pd.Series, max_periods: int = 5) -> dict:
    periods = list(income_stmt.columns[:max_periods])
    periods_sorted = sorted(periods)  # 古い順にして推移として見やすくする

    revenue = _row(income_stmt, "Total Revenue")
    gross_profit = _row(income_stmt, "Gross Profit")
    operating_income = _row(income_stmt, "Operating Income")
    net_income = _row(income_stmt, "Net Income")
    basic_eps = _row(income_stmt, "Basic EPS")
    shares_out = _row(income_stmt, "Basic Average Shares")

    total_assets = _row(balance_sheet, "Total Assets")
    stockholders_equity = _row(balance_sheet, "Stockholders Equity")
    ordinary_shares = _row(balance_sheet, "Ordinary Shares Number")

    op_cf = _row(cashflow, "Operating Cash Flow")
    inv_cf = _row(cashflow, "Investing Cash Flow")
    fin_cf = _row(cashflow, "Financing Cash Flow")
    free_cf = _row(cashflow, "Free Cash Flow")

    dps_by_period = _dividend_per_share_by_period(dividends, periods_sorted)

    timeline = []
    def _valid(x):
        return x is not None and not pd.isna(x)

    def _div(a, b):
        return (a / b) if _valid(a) and _valid(b) and b != 0 else None

    for period in periods_sorted:
        rev = revenue.get(period)
        gp = gross_profit.get(period)
        oi = operating_income.get(period)
        ni = net_income.get(period)
        eq = stockholders_equity.get(period)
        ta = total_assets.get(period)
        eps = basic_eps.get(period)
        dps = dps_by_period.get(period)
        shares = ordinary_shares.get(period)

        entry = {
            "period": _fiscal_year_label(period),
            "revenue": rev if _valid(rev) else None,
            "operating_income": oi if _valid(oi) else None,
            "net_income": ni if _valid(ni) else None,
            "gross_margin": _div(gp, rev),
            "operating_margin": _div(oi, rev),
            "net_margin": _div(ni, rev),
            "roe": _div(ni, eq),
            "roa": _div(ni, ta),
            "equity_ratio": _div(eq, ta),
            "eps": eps if _valid(eps) else None,
            "bps": _div(eq, shares),
            "dividend_per_share": dps,
            "payout_ratio": _div(dps, eps),
            "operating_cf": op_cf.get(period) if _valid(op_cf.get(period)) else None,
            "investing_cf": inv_cf.get(period) if _valid(inv_cf.get(period)) else None,
            "financing_cf": fin_cf.get(period) if _valid(fin_cf.get(period)) else None,
            "free_cf": free_cf.get(period) if _valid(free_cf.get(period)) else None,
        }
        if not _valid(rev) and not _valid(ni):
            continue  # データのない期（yfinanceの取得上限による空列）は除外
        timeline.append(entry)

    latest = timeline[-1] if timeline else {}
    revenue_trend = [t["revenue"] for t in timeline if t["revenue"] is not None]
    net_income_trend = [t["net_income"] for t in timeline if t["net_income"] is not None]

    is_growing_revenue = len(revenue_trend) >= 2 and revenue_trend[-1] > revenue_trend[-2]
    is_growing_profit = len(net_income_trend) >= 2 and net_income_trend[-1] > net_income_trend[-2]

    return {
        "timeline": timeline,
        "latest": latest,
        "trend_flags": {
            "revenue_yoy_growth": is_growing_revenue,
            "net_income_yoy_growth": is_growing_profit,
            "zoushu_zoueki": is_growing_revenue and is_growing_profit,  # 増収増益
        },
    }
