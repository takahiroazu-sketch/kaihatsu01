"""
Phase 1: データ取得基盤

日本株の証券コード（4桁）を1つ渡すと、yfinance経由で
- 株価データ（日足）
- 財務データ（損益計算書・貸借対照表・キャッシュフロー計算書）
- 主要指標（PER, PBR, 配当利回り等）
を取得し、data/ 配下にキャッシュ保存する疎通確認スクリプト。

使い方:
    python3 fetch_data.py 7203
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).parent / "data"


def to_yahoo_ticker(code: str) -> str:
    """4桁の証券コードをyfinance用ティッカー（例: 7203 -> 7203.T）に変換する。"""
    code = code.strip().upper()
    return code if "." in code else f"{code}.T"


def fetch(code: str) -> dict:
    ticker_symbol = to_yahoo_ticker(code)
    ticker = yf.Ticker(ticker_symbol)

    info = ticker.info
    history = ticker.history(period="1y")
    income_stmt = ticker.income_stmt
    balance_sheet = ticker.balance_sheet
    cashflow = ticker.cashflow
    dividends = ticker.dividends if ticker.dividends is not None else pd.Series(dtype=float)

    if history.empty:
        raise ValueError(f"証券コード '{code}' の株価データが見つかりませんでした。コードが正しいか確認してください。")

    return {
        "ticker_symbol": ticker_symbol,
        "info": info,
        "history": history,
        "income_stmt": income_stmt,
        "balance_sheet": balance_sheet,
        "cashflow": cashflow,
        "dividends": dividends,
    }


def summarize(result: dict) -> dict:
    info = result["info"]
    history = result["history"]

    latest_close = float(history["Close"].iloc[-1]) if not history.empty else None

    return {
        "ticker_symbol": result["ticker_symbol"],
        "company_name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "latest_close": latest_close,
        "currency": info.get("currency"),
        "trailing_per": info.get("trailingPE"),
        "forward_per": info.get("forwardPE"),
        "pbr": info.get("priceToBook"),
        "dividend_yield": info.get("dividendYield"),
        "roe": info.get("returnOnEquity"),
        "market_cap": info.get("marketCap"),
        "history_rows": len(history),
        "income_stmt_periods": list(result["income_stmt"].columns.astype(str)) if not result["income_stmt"].empty else [],
        "dividend_rows": len(result["dividends"]),
    }


def save_cache(code: str, result: dict) -> Path:
    out_dir = DATA_DIR / code
    out_dir.mkdir(parents=True, exist_ok=True)

    result["history"].to_csv(out_dir / "history.csv")
    result["income_stmt"].to_csv(out_dir / "income_stmt.csv")
    result["balance_sheet"].to_csv(out_dir / "balance_sheet.csv")
    result["cashflow"].to_csv(out_dir / "cashflow.csv")
    result["dividends"].to_csv(out_dir / "dividends.csv")

    with open(out_dir / "info.json", "w", encoding="utf-8") as f:
        json.dump(result["info"], f, ensure_ascii=False, indent=2, default=str)

    return out_dir


def main():
    parser = argparse.ArgumentParser(description="証券コードから株価・財務データを取得する（Phase 1 疎通確認）")
    parser.add_argument("code", help="証券コード（例: 7203）")
    args = parser.parse_args()

    print(f"[fetch] {args.code} のデータを取得中...")
    try:
        result = fetch(args.code)
    except Exception as e:
        print(f"[error] データ取得に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    summary = summarize(result)
    print("\n=== 取得結果サマリー ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    out_dir = save_cache(args.code, result)
    print(f"\n[saved] {out_dir} にキャッシュ保存しました。")


if __name__ == "__main__":
    main()
