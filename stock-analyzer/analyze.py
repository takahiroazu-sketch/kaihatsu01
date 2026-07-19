"""
Phase 2: 分析ロジック

証券コードを1つ渡すと、fetch_data.fetch() で取得したデータをもとに
ファンダメンタルズ・バリュエーション・テクニカルの3分析を計算し、結果を表示・保存する。

使い方:
    python3 analyze.py 7203
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from fetch_data import fetch
from analysis.fundamentals import compute_fundamentals
from analysis.valuation import compute_valuation
from analysis.technical import compute_technical

DATA_DIR = Path(__file__).parent / "data"


def _has_value(x):
    return isinstance(x, (int, float)) and not pd.isna(x)


def _pct(x):
    return f"{x * 100:.1f}%" if _has_value(x) else "N/A"


def _num(x, unit=""):
    return f"{x:,.1f}{unit}" if _has_value(x) else "N/A"


def print_report(code: str, fundamentals: dict, valuation: dict, technical: dict):
    print(f"\n{'=' * 50}")
    print(f" 銘柄分析レポート: {code}")
    print(f"{'=' * 50}")

    print("\n--- 1. ファンダメンタルズ分析 ---")
    for row in fundamentals["timeline"]:
        print(f"  [{row['period']}] 売上高: {_num(row['revenue'])}  "
              f"営業益: {_num(row['operating_income'])}  純利益: {_num(row['net_income'])}  "
              f"ROE: {_pct(row['roe'])}  EPS: {_num(row['eps'])}")
    flags = fundamentals["trend_flags"]
    print(f"  増収: {flags['revenue_yoy_growth']} / 増益: {flags['net_income_yoy_growth']} "
          f"/ 増収増益: {flags['zoushu_zoueki']}")

    print("\n--- 2. バリュエーション分析 ---")
    print(f"  株価: {_num(valuation['latest_close'], '円')}")
    print(f"  PER(実績): {_num(valuation['trailing_per'])}倍  PER(予想): {_num(valuation['forward_per'])}倍")
    print(f"  PBR: {_num(valuation['pbr'])}倍  PSR: {_num(valuation['psr'])}倍  "
          f"EV/EBITDA: {_num(valuation['ev_to_ebitda'])}倍")
    print(f"  配当利回り: {_pct(valuation['dividend_yield'])}")
    print(f"  簡易理論株価(配当割引モデル): {_num(valuation['theoretical_price_ddm'], '円')}")

    print("\n--- 3. テクニカル分析 ---")
    ma = technical["moving_averages"]
    print(f"  終値({technical['latest_date']}): {_num(technical['latest_close'], '円')}")
    print(f"  MA5: {_num(ma['ma5'])}  MA25: {_num(ma['ma25'])}  MA75: {_num(ma['ma75'])}  MA200: {_num(ma['ma200'])}")
    print(f"  RSI(14): {_num(technical['rsi_14'])}")
    macd = technical["macd"]
    print(f"  MACD: {_num(macd['macd'])}  シグナル: {_num(macd['signal'])}  ヒストグラム: {_num(macd['histogram'])}")
    cross = technical["cross_signal"]
    print(f"  直近クロス({cross['ma_pair']}): {cross['type']}（{cross['date']}）")
    sr = technical["support_resistance"]
    print(f"  52週高値: {_num(sr['range_52w_high'], '円')}  52週安値: {_num(sr['range_52w_low'], '円')}")


def main():
    parser = argparse.ArgumentParser(description="証券コードから3分析（ファンダメンタルズ/バリュエーション/テクニカル）を実行する")
    parser.add_argument("code", help="証券コード（例: 7203）")
    args = parser.parse_args()

    print(f"[analyze] {args.code} のデータを取得・分析中...")
    try:
        result = fetch(args.code)
    except Exception as e:
        print(f"[error] データ取得に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    fundamentals = compute_fundamentals(
        result["income_stmt"], result["balance_sheet"], result["cashflow"], result["dividends"]
    )
    valuation = compute_valuation(result["info"], result["history"], result["dividends"])
    technical = compute_technical(result["history"])

    print_report(args.code, fundamentals, valuation, technical)

    out_dir = DATA_DIR / args.code
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "analysis.json", "w", encoding="utf-8") as f:
        json.dump(
            {"fundamentals": fundamentals, "valuation": valuation, "technical": technical},
            f, ensure_ascii=False, indent=2, default=str,
        )
    print(f"\n[saved] {out_dir / 'analysis.json'} に分析結果を保存しました。")


if __name__ == "__main__":
    main()
