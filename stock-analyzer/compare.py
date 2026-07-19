"""
拡張: 複数銘柄比較

証券コードを複数渡すと、それぞれ取得・分析した上で指標を横並び比較するダッシュボード(HTML)を生成する。

使い方:
    python3 compare.py 7203 6758 8306
"""

import argparse
import sys
from pathlib import Path

from fetch_data import fetch
from analysis.fundamentals import compute_fundamentals
from analysis.valuation import compute_valuation
from analysis.technical import compute_technical
from dashboard.compare_render import render_comparison

OUTPUT_DIR = Path(__file__).parent / "output"


def main():
    parser = argparse.ArgumentParser(description="複数の証券コードを比較するダッシュボード(HTML)を生成する")
    parser.add_argument("codes", nargs="+", help="証券コード（例: 7203 6758 8306）")
    args = parser.parse_args()

    entries = []
    for code in args.codes:
        print(f"[compare] {code} のデータを取得・分析中...")
        try:
            result = fetch(code)
        except Exception as e:
            print(f"[error] {code}: データ取得に失敗しました: {e}", file=sys.stderr)
            sys.exit(1)

        fundamentals = compute_fundamentals(
            result["income_stmt"], result["balance_sheet"], result["cashflow"], result["dividends"]
        )
        valuation = compute_valuation(result["info"], result["history"], result["dividends"])
        technical = compute_technical(result["history"])

        entries.append({
            "code": code, "info": result["info"],
            "fundamentals": fundamentals, "valuation": valuation, "technical": technical,
        })

    html = render_comparison(entries)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"compare_{'_'.join(args.codes)}.html"
    out_path.write_text(html, encoding="utf-8")

    print(f"[saved] {out_path}")


if __name__ == "__main__":
    main()
