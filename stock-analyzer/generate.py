"""
一括生成: ダッシュボード(HTML) + レポート(PDF)

証券コードを1つ以上渡すと、それぞれ取得・分析した上で
ダッシュボード(HTML)とレポート(PDF)の両方を自動生成する。
データ取得・分析は銘柄ごとに1回だけ行い、その結果を両方の出力で共有する。

使い方:
    python3 generate.py 7203
    python3 generate.py 7203 6758 8306
"""

import argparse
import sys
from pathlib import Path

from fetch_data import fetch
from analysis.fundamentals import compute_fundamentals
from analysis.valuation import compute_valuation
from analysis.technical import compute_technical
from dashboard.render import render_dashboard
from dashboard.pdf_report import build_pdf

OUTPUT_DIR = Path(__file__).parent / "output"


def generate_one(code: str):
    print(f"[generate] {code} のデータを取得・分析中...")
    result = fetch(code)

    fundamentals = compute_fundamentals(
        result["income_stmt"], result["balance_sheet"], result["cashflow"], result["dividends"]
    )
    valuation = compute_valuation(result["info"], result["history"], result["dividends"])
    technical = compute_technical(result["history"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    html = render_dashboard(code, result["info"], result["history"], fundamentals, valuation, technical)
    html_path = OUTPUT_DIR / f"{code}_dashboard.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  [saved] {html_path}")

    pdf_path = OUTPUT_DIR / f"{code}_report.pdf"
    build_pdf(code, result["info"], result["history"], fundamentals, valuation, technical, str(pdf_path))
    print(f"  [saved] {pdf_path}")


def main():
    parser = argparse.ArgumentParser(
        description="証券コードからダッシュボード(HTML)とレポート(PDF)を一括生成する"
    )
    parser.add_argument("codes", nargs="+", help="証券コード（例: 7203 6758 8306）")
    args = parser.parse_args()

    failed = []
    for code in args.codes:
        try:
            generate_one(code)
        except Exception as e:
            print(f"[error] {code}: 生成に失敗しました: {e}", file=sys.stderr)
            failed.append(code)

    if failed:
        print(f"\n[warning] 失敗した銘柄コード: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
