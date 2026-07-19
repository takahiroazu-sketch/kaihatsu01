"""
Phase 3: ダッシュボード生成

証券コードを1つ渡すと、データ取得→3分析→HTMLダッシュボード生成までを一括実行する。

使い方:
    python3 generate_dashboard.py 7203
"""

import argparse
import sys
from pathlib import Path

from fetch_data import fetch
from analysis.fundamentals import compute_fundamentals
from analysis.valuation import compute_valuation
from analysis.technical import compute_technical
from dashboard.render import render_dashboard

OUTPUT_DIR = Path(__file__).parent / "output"


def main():
    parser = argparse.ArgumentParser(description="証券コードから銘柄分析ダッシュボード(HTML)を生成する")
    parser.add_argument("code", help="証券コード（例: 7203）")
    args = parser.parse_args()

    print(f"[dashboard] {args.code} のデータを取得・分析中...")
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

    html = render_dashboard(
        args.code, result["info"], result["history"], fundamentals, valuation, technical
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{args.code}_dashboard.html"
    out_path.write_text(html, encoding="utf-8")

    print(f"[saved] {out_path}")


if __name__ == "__main__":
    main()
