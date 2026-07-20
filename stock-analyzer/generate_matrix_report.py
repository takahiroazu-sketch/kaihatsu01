"""
拡張: 保有銘柄マトリクスレポート

holdings.csv の選択銘柄（run_holdings.py と同じ対象）をすべて取得・分析し、
個別銘柄ごとのダッシュボード/レポートとは別に、全銘柄の主要指標を1つの表（マトリクス）に
まとめたPDFレポートを1本生成する。承認済みPDFデザインスタイルを踏襲する。

使い方:
    python3 generate_matrix_report.py
    python3 generate_matrix_report.py --file holdings.csv
"""

import argparse
import io
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

from fetch_data import fetch
from analysis.fundamentals import compute_fundamentals
from analysis.valuation import compute_valuation
from analysis.technical import compute_technical
from run_holdings import load_selected, HOLDINGS_PATH
from dashboard import pdf_report
from dashboard.pdf_report import (
    new_page, gs_content, make_table, POS, NEG,
    _fmt_yen, _fmt_pct, _fmt_ratio,
)
from dashboard.charts import BG, TEXT, TEXT2, TEAL

OUTPUT_DIR = Path(__file__).parent / "output"
OUT_PATH = OUTPUT_DIR / "holdings_matrix_report.pdf"
ROWS_PER_PAGE = 20

VERSION_DATE = datetime.now().strftime("%Y年%m月%d日")
FOOTER_LABEL = f"保有銘柄一覧レポート  {VERSION_DATE}"

_CROSS_LABEL = {"golden_cross": "ゴールデンクロス", "dead_cross": "デッドクロス"}


def collect(entries: list[tuple[str, str, str]]) -> tuple[list[dict], list[str]]:
    """holdings.csvの選択銘柄を取得・分析し、マトリクス用の行データに変換する。"""
    rows, failed = [], []
    for code, name, industry in entries:
        print(f"[matrix] {code} のデータを取得・分析中...")
        try:
            result = fetch(code)
        except Exception as e:
            print(f"[error] {code}: データ取得に失敗しました: {e}", file=sys.stderr)
            failed.append(code)
            continue

        fundamentals = compute_fundamentals(
            result["income_stmt"], result["balance_sheet"], result["cashflow"], result["dividends"]
        )
        valuation = compute_valuation(result["info"], result["history"], result["dividends"])
        technical = compute_technical(result["history"])

        rows.append({
            "code": code,
            "name": name or result["info"].get("longName") or code,
            "industry": industry or result["info"].get("sector") or "―",
            "latest_close": technical["latest_close"],
            "per": valuation["trailing_per"],
            "pbr": valuation["pbr"],
            "dividend_yield": valuation["dividend_yield"],
            "roe": fundamentals["latest"].get("roe"),
            "cross": technical["cross_signal"]["type"],
        })
    return rows, failed


# ── 1. 表紙 ──────────────────────────────────────────────────
def page_cover(row_count: int, failed_count: int):
    pdf_report._PAGE_NUM[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)

    left = fig.add_axes([0, 0.12, 0.38, 0.78])
    left.set_xlim(0, 1)
    left.set_ylim(0, 1)
    left.axis("off")
    left.add_patch(Rectangle((0, 0), 1, 1, facecolor=TEAL, edgecolor="none", transform=left.transAxes))

    fig.text(0.44, 0.80, "保有銘柄一覧", fontsize=28, fontweight="bold", color=TEXT, va="center")
    fig.text(0.44, 0.70, "マトリクスレポート", fontsize=28, fontweight="bold", color=TEXT, va="center")
    fig.text(0.44, 0.60, f"作成日: {VERSION_DATE}", fontsize=12, color=TEXT2, va="center")

    kpis = [(str(row_count), "集計銘柄数", TEXT)]
    if failed_count:
        kpis.append((str(failed_count), "取得失敗銘柄数", NEG))
    for i, (val, lbl, clr) in enumerate(kpis):
        ky = 0.48 - i * 0.085
        fig.text(0.44, ky, val, fontsize=20, fontweight="bold", color=clr, va="center")
        fig.text(0.53, ky, lbl, fontsize=11, color=TEXT2, va="center")

    fig.text(0.44, 0.30, "個別銘柄ごとのダッシュボード(HTML)／レポート(PDF)とは別に、\n"
                          "保有銘柄すべての主要指標を1つの表に並べて横断比較できるようにしたレポートです。",
              fontsize=10, color=TEXT2, va="center")

    div = fig.add_axes([0.44, 0.155, 0.52, 0.002])
    div.set_facecolor("#C8C4BE")
    div.axis("off")

    fig.text(0.44, 0.12,
              "本レポートはholdings.csvで選択された銘柄の分析結果を提示するものであり、\n"
              "ツール側から独自の銘柄推奨は行いません。投資判断はご自身の責任で行ってください。",
              fontsize=8.5, color=TEXT2, va="center")

    foot = fig.add_axes([0, 0, 1, 0.075])
    foot.set_facecolor("#1C1C1C")
    foot.axis("off")
    foot.set_xlim(0, 1)
    foot.set_ylim(0, 1)
    foot.text(0.5, 0.45, FOOTER_LABEL, ha="center", color="#909090", fontsize=8, va="center")
    foot.text(0.96, 0.45, str(pdf_report._PAGE_NUM[0]), color="#D0D0D0", fontsize=11,
              fontweight="bold", ha="right", va="center")

    return fig


# ── 2. マトリクス本体（複数ページに分割） ─────────────────────
def page_matrix(rows_chunk: list[dict], page_no: int, total_pages: int):
    fig = new_page(FOOTER_LABEL, label=f"指標マトリクス（{page_no}/{total_pages}ページ）",
                    title="保有銘柄 指標マトリクス",
                    insight="株価・PER・PBR・配当利回り・ROE・直近クロスを銘柄横断で一覧表示")
    gs = gs_content(fig, 1, 1, top=0.78, bottom=0.10)
    ax = fig.add_subplot(gs[0, 0])
    ax.set_facecolor(BG)
    ax.axis("off")

    headers = ["銘柄", "業種", "コード", "株価", "PER（実績）", "PBR", "配当利回り", "ROE（最新期）", "直近クロス"]
    table_rows, cell_colors = [], {}
    for i, r in enumerate(rows_chunk):
        row_idx = i + 1
        table_rows.append([
            r["name"], r["industry"], r["code"], _fmt_yen(r["latest_close"]), _fmt_ratio(r["per"]),
            _fmt_ratio(r["pbr"]), _fmt_pct(r["dividend_yield"]), _fmt_pct(r["roe"]),
            _CROSS_LABEL.get(r["cross"], "―"),
        ])
        if isinstance(r["roe"], (int, float)):
            cell_colors[(row_idx, 7)] = POS if r["roe"] >= 0 else NEG
        if r["cross"] == "golden_cross":
            cell_colors[(row_idx, 8)] = POS
        elif r["cross"] == "dead_cross":
            cell_colors[(row_idx, 8)] = NEG

    col_w = [0.15, 0.14, 0.07, 0.09, 0.10, 0.07, 0.10, 0.11, 0.12]
    make_table(ax, headers, table_rows, col_w=col_w, fs=8.5, row_scale=1.5, cell_colors=cell_colors)

    return fig


def build(entries: list[tuple[str, str]]):
    rows, failed = collect(entries)
    if not rows:
        return None, failed

    pdf_report._reset_page_num()
    total_pages = -(-len(rows) // ROWS_PER_PAGE)  # 切り上げ除算
    pages = [page_cover(len(rows), len(failed))]
    for i in range(total_pages):
        chunk = rows[i * ROWS_PER_PAGE:(i + 1) * ROWS_PER_PAGE]
        pages.append(page_matrix(chunk, i + 1, total_pages))

    a4w, a4h = int(297 * 150 / 25.4), int(210 * 150 / 25.4)
    imgs = []
    for fig in pages:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        imgs.append(Image.open(buf).convert("RGB").resize((a4w, a4h), Image.LANCZOS))
        plt.close(fig)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    imgs[0].save(OUT_PATH, save_all=True, append_images=imgs[1:], resolution=150)
    return OUT_PATH, failed


def main():
    parser = argparse.ArgumentParser(
        description="保有銘柄一覧(holdings.csv)から全銘柄横断のマトリクスPDFレポートを生成する"
    )
    parser.add_argument("--file", default=str(HOLDINGS_PATH), help="保有銘柄一覧CSVのパス（既定: holdings.csv）")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"[error] 保有銘柄一覧が見つかりません: {path}", file=sys.stderr)
        sys.exit(1)

    entries = load_selected(path)
    if not entries:
        print(f"[warning] {path} の「選択」列が1の銘柄がありません。")
        return

    print(f"[matrix] {len(entries)}銘柄のマトリクスレポートを作成します")
    out_path, failed = build(entries)

    if out_path:
        print(f"[saved] {out_path}")
    if failed:
        print(f"[warning] 取得に失敗した銘柄: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
