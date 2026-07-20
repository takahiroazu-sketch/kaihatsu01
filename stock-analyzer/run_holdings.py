"""
拡張: 保有銘柄一覧からの一括解析

holdings.csv（保有銘柄一覧）を読み込み、「選択」列が1の銘柄だけを
generate.py と同じ処理（データ取得→3分析→ダッシュボード(HTML)+レポート(PDF)生成）でまとめて解析する。

使い方:
    python3 run_holdings.py
    python3 run_holdings.py --file holdings.csv
"""

import argparse
import csv
import sys
from pathlib import Path

from generate import generate_one

HOLDINGS_PATH = Path(__file__).parent / "holdings.csv"


def load_selected(path: Path) -> list[tuple[str, str, str]]:
    """holdings.csvから「選択」列が1の行の (証券コード/ティッカー, 銘柄名称, 業種) を返す。"""
    entries = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if (row.get("選択") or "").strip() != "1":
                continue
            code = (row.get("ティッカー") or "").strip() or (row.get("証券コード") or "").strip()
            if not code:
                continue
            entries.append((
                code,
                (row.get("銘柄名称") or "").strip(),
                (row.get("業種") or "").strip(),
            ))
    return entries


def main():
    parser = argparse.ArgumentParser(
        description="保有銘柄一覧(holdings.csv)で選択された銘柄をまとめて解析・生成する"
    )
    parser.add_argument("--file", default=str(HOLDINGS_PATH), help="保有銘柄一覧CSVのパス（既定: holdings.csv）")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"[error] 保有銘柄一覧が見つかりません: {path}", file=sys.stderr)
        sys.exit(1)

    entries = load_selected(path)
    if not entries:
        print(f"[warning] {path} の「選択」列に印が付いた銘柄がありません。")
        return

    print(f"[holdings] {len(entries)}銘柄を解析します: {', '.join(code for code, _, _ in entries)}")

    failed = []
    for code, name, _industry in entries:
        label = f"{code}（{name}）" if name else code
        print(f"\n--- {label} ---")
        try:
            generate_one(code)
        except Exception as e:
            print(f"[error] {label}: 生成に失敗しました: {e}", file=sys.stderr)
            failed.append(label)

    if failed:
        print(f"\n[warning] 失敗した銘柄: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
