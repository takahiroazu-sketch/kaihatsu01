"""PDFレポート生成。

承認済みPDFデザインスタイル（design_pdf_style: オフホワイト背景・黒フッター・ティールアクセント、
shisan_kanri/create_dividend_pdf_v4.py で採用）のページ構成をそのまま踏襲する。
"""

import io
import os
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec
from PIL import Image

from dashboard.charts import (
    BG, TEXT, TEXT2, TEAL, AMBER, GRID, SPINE,
    draw_revenue_profit, draw_price_ma, draw_rsi,
)

POS = "#2D8A50"
NEG = "#C03030"
FOOTER = "#1C1C1C"
HDRBG = "#D4D0CC"
ALTBG = "#F5F2EE"

_PAGE_NUM = [0]


def _reset_page_num():
    _PAGE_NUM[0] = 0


def _footer_label(company_name: str, code: str) -> str:
    date_str = datetime.now().strftime("%Y年%m月%d日")
    return f"{company_name}（{code}）  銘柄分析レポート  {date_str}"


def new_page(footer_label: str, label="", title="", insight=""):
    """背景BG・ヘッダーバーなし・下部黒フッターの標準ページ。"""
    _PAGE_NUM[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)

    if label:
        fig.text(0.04, 0.935, label, fontsize=9.5, color=TEXT2, va="center")
    if title:
        fig.text(0.04, 0.885, title, fontsize=16, color=TEXT, fontweight="bold", va="center")
    if insight:
        fig.text(0.04, 0.840, insight, fontsize=10, color=TEXT2, va="center")

    hline = fig.add_axes([0.04, 0.822, 0.92, 0.002])
    hline.set_facecolor("#C8C4BE")
    hline.axis("off")

    foot = fig.add_axes([0, 0, 1, 0.075])
    foot.set_facecolor(FOOTER)
    foot.axis("off")
    foot.set_xlim(0, 1)
    foot.set_ylim(0, 1)
    foot.text(0.04, 0.45, footer_label, color="#909090", fontsize=8, va="center")
    foot.text(0.96, 0.45, str(_PAGE_NUM[0]), color="#D0D0D0", fontsize=11, fontweight="bold", ha="right", va="center")

    return fig


def gs_content(fig, nrows=1, ncols=1, hspace=0.45, wspace=0.30, top=0.810, bottom=0.105):
    return GridSpec(nrows, ncols, figure=fig, left=0.04, right=0.97, bottom=bottom, top=top,
                     hspace=hspace, wspace=wspace)


def make_table(ax, headers, rows, col_w=None, fs=9.5, row_scale=1.7, cell_colors=None):
    """水平線のみのテーブル。cell_colors: {(row_idx, col_idx): color} でテキスト色を上書き（0行目=ヘッダー）。"""
    kw = dict(cellText=rows, colLabels=headers, cellLoc="center", loc="center")
    if col_w:
        kw["colWidths"] = col_w
    t = ax.table(**kw)
    t.auto_set_font_size(False)
    t.set_fontsize(fs)
    t.scale(1, row_scale)
    for (r, c), cell in t.get_celld().items():
        cell.set_linewidth(0.4)
        if r == 0:
            cell.set_facecolor(HDRBG)
            cell.set_edgecolor("#B8B4B0")
            cell.get_text().set_color(TEXT)
            cell.get_text().set_fontweight("bold")
        elif r % 2 == 0:
            cell.set_facecolor(ALTBG)
            cell.set_edgecolor("#D0CCC8")
        else:
            cell.set_facecolor(BG)
            cell.set_edgecolor("#D0CCC8")
        if cell_colors and (r, c) in cell_colors:
            cell.get_text().set_color(cell_colors[(r, c)])
    ax.axis("off")
    return t


def _fmt_yen(v):
    return f"{v:,.0f}円" if isinstance(v, (int, float)) else "―"


def _fmt_oku(v):
    return f"{v / 1e8:,.0f}億円" if isinstance(v, (int, float)) else "―"


def _fmt_pct(v):
    return f"{v * 100:.1f}%" if isinstance(v, (int, float)) else "―"


def _fmt_ratio(v):
    return f"{v:.1f}倍" if isinstance(v, (int, float)) else "―"


def _fmt_num(v):
    return f"{v:,.1f}" if isinstance(v, (int, float)) else "―"


# ── 1. 表紙 ──────────────────────────────────────────────────
def page_cover(footer_label, code, info, fundamentals, valuation, technical):
    _PAGE_NUM[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)

    left = fig.add_axes([0, 0.12, 0.38, 0.78])
    left.set_xlim(0, 1)
    left.set_ylim(0, 1)
    left.axis("off")
    left.add_patch(Rectangle((0, 0), 1, 1, facecolor=TEAL, edgecolor="none", transform=left.transAxes))

    company_name = info.get("longName") or code
    sector = info.get("sector") or "―"
    industry = info.get("industry") or "―"

    fig.text(0.44, 0.80, "銘柄分析", fontsize=30, fontweight="bold", color=TEXT, va="center")
    fig.text(0.44, 0.70, "レポート", fontsize=30, fontweight="bold", color=TEXT, va="center")
    fig.text(0.44, 0.60, f"{company_name}（{code}） ／ {sector} - {industry}",
             fontsize=13, color=TEXT2, va="center")

    latest = fundamentals["latest"]
    kpis = [
        (_fmt_yen(technical["latest_close"]), "終値", TEXT),
        (_fmt_ratio(valuation["trailing_per"]), "PER（実績）", TEAL),
        (_fmt_ratio(valuation["pbr"]), "PBR", AMBER),
        (_fmt_pct(valuation["dividend_yield"]), "配当利回り", POS),
        (_fmt_pct(latest.get("roe")), "ROE（最新期）", TEXT),
    ]
    for i, (val, lbl, clr) in enumerate(kpis):
        ky = 0.46 - i * 0.075
        fig.text(0.44, ky, val, fontsize=16, fontweight="bold", color=clr, va="center")
        fig.text(0.67, ky, lbl, fontsize=10, color=TEXT2, va="center")

    div = fig.add_axes([0.44, 0.135, 0.52, 0.002])
    div.set_facecolor("#C8C4BE")
    div.axis("off")

    fig.text(0.44, 0.105,
              "本レポートはユーザーが指定した銘柄コードの分析結果を提示するものであり、\n"
              "ツール側から独自の銘柄推奨は行いません。投資判断はご自身の責任で行ってください。",
              fontsize=8.5, color=TEXT2, va="center")

    foot = fig.add_axes([0, 0, 1, 0.075])
    foot.set_facecolor(FOOTER)
    foot.axis("off")
    foot.set_xlim(0, 1)
    foot.set_ylim(0, 1)
    foot.text(0.5, 0.45, footer_label, ha="center", color="#909090", fontsize=8, va="center")
    foot.text(0.96, 0.45, "1", color="#D0D0D0", fontsize=11, fontweight="bold", ha="right", va="center")

    return fig


# ── 2. ファンダメンタルズ ────────────────────────────────────
def page_fundamentals(footer_label, fundamentals):
    timeline = fundamentals["timeline"]
    flags = fundamentals["trend_flags"]
    zoushu_zoueki = "増収増益" if flags["zoushu_zoueki"] else (
        ("増収" if flags["revenue_yoy_growth"] else "減収") + "・" +
        ("増益" if flags["net_income_yoy_growth"] else "減益")
    )

    fig = new_page(footer_label, label="ファンダメンタルズ分析",
                    title="売上・利益・収益性の推移",
                    insight=f"直近期は{zoushu_zoueki}（前期比）")
    gs = gs_content(fig, 2, 1, hspace=0.55, top=0.78)

    ax1 = fig.add_subplot(gs[0, 0])
    draw_revenue_profit(ax1, timeline)

    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor(BG)
    ax2.axis("off")
    ax2.set_title("期別 財務指標", fontsize=11, fontweight="bold", color=TEXT, pad=10, loc="left")

    headers = ["期", "売上高", "営業利益", "純利益", "営業利益率", "純利益率", "ROE", "EPS", "配当/株"]
    rows, cell_colors = [], {}
    for i, t in enumerate(timeline):
        row_idx = i + 1
        rows.append([
            t["period"], _fmt_oku(t["revenue"]), _fmt_oku(t["operating_income"]), _fmt_oku(t["net_income"]),
            _fmt_pct(t["operating_margin"]), _fmt_pct(t["net_margin"]), _fmt_pct(t["roe"]),
            f"{_fmt_num(t['eps'])}円", f"{_fmt_num(t['dividend_per_share'])}円",
        ])
        for col_idx, key in ((2, "operating_income"), (3, "net_income"), (6, "roe")):
            v = t[key]
            if isinstance(v, (int, float)):
                cell_colors[(row_idx, col_idx)] = POS if v >= 0 else NEG

    make_table(ax2, headers, rows, col_w=[0.10, 0.13, 0.13, 0.13, 0.12, 0.12, 0.10, 0.09, 0.09],
               fs=9.5, row_scale=1.9, cell_colors=cell_colors)

    return fig


# ── 3. バリュエーション ──────────────────────────────────────
def page_valuation(footer_label, valuation):
    fig = new_page(footer_label, label="バリュエーション分析",
                    title="株価水準の評価",
                    insight="PER・PBR等の市場評価指標と、簡易配当割引モデルによる参考理論株価")
    gs = gs_content(fig, 1, 2, wspace=0.35, top=0.78)

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(BG)
    ax1.axis("off")
    ax1.set_title("評価指標一覧", fontsize=11, fontweight="bold", color=TEXT, pad=10, loc="left")
    headers = ["指標", "値"]
    rows = [
        ["株価", _fmt_yen(valuation["latest_close"])],
        ["PER（実績）", _fmt_ratio(valuation["trailing_per"])],
        ["PER（予想）", _fmt_ratio(valuation["forward_per"])],
        ["PBR", _fmt_ratio(valuation["pbr"])],
        ["PSR", _fmt_ratio(valuation["psr"])],
        ["EV/EBITDA", _fmt_ratio(valuation["ev_to_ebitda"])],
        ["配当利回り", _fmt_pct(valuation["dividend_yield"])],
    ]
    make_table(ax1, headers, rows, col_w=[0.55, 0.45], fs=10.5, row_scale=2.0)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(BG)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    ax2.add_patch(Rectangle((0, 0), 1, 1, facecolor=ALTBG, edgecolor=GRID, lw=0.8, transform=ax2.transAxes))
    ax2.text(0.08, 0.88, "簡易理論株価（配当割引モデル）", fontsize=11, fontweight="bold",
             color=TEXT, transform=ax2.transAxes)

    theoretical = valuation.get("theoretical_price_ddm")
    ax2.text(0.08, 0.72, _fmt_yen(theoretical), fontsize=22, fontweight="bold", color=TEAL,
             transform=ax2.transAxes)

    assumptions = valuation.get("ddm_assumptions") or {}
    if assumptions:
        note = (f"要求利回り: {_fmt_pct(assumptions.get('required_return'))}\n"
                f"想定配当成長率: {_fmt_pct(assumptions.get('dividend_growth_rate'))}\n\n"
                "※ 簡易モデルによる参考値であり、実際の企業価値評価とは\n"
                "異なる場合があります。投資判断はご自身の責任で\n行ってください。")
    else:
        note = "配当実績がないため、本モデルでは算出していません。"
    ax2.text(0.08, 0.56, note, fontsize=9.5, color=TEXT2, va="top", transform=ax2.transAxes)

    return fig


# ── 4. テクニカル ────────────────────────────────────────────
def page_technical(footer_label, history, technical):
    cross = technical["cross_signal"]
    fig = new_page(footer_label, label="テクニカル分析",
                    title="株価推移とシグナル",
                    insight=f"直近クロス（{cross['ma_pair']}）: {cross['type'] or '―'}（{cross['date'] or '―'}）")
    gs = gs_content(fig, 2, 2, hspace=0.5, wspace=0.3, top=0.78)

    ax1 = fig.add_subplot(gs[0, :])
    draw_price_ma(ax1, history)

    ax2 = fig.add_subplot(gs[1, 0])
    draw_rsi(ax2, history)

    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor(BG)
    ax3.axis("off")
    ax3.set_title("指標サマリー", fontsize=11, fontweight="bold", color=TEXT, pad=10, loc="left")

    ma = technical["moving_averages"]
    macd = technical["macd"]
    sr = technical["support_resistance"]
    vol = technical["volume"]
    headers = ["項目", "値"]
    rows = [
        ["MA5 / MA25", f"{_fmt_yen(ma['ma5'])} / {_fmt_yen(ma['ma25'])}"],
        ["MA75 / MA200", f"{_fmt_yen(ma['ma75'])} / {_fmt_yen(ma['ma200'])}"],
        ["RSI(14)", _fmt_num(technical["rsi_14"])],
        ["MACD / シグナル", f"{_fmt_num(macd['macd'])} / {_fmt_num(macd['signal'])}"],
        ["52週高値 / 安値", f"{_fmt_yen(sr['range_52w_high'])} / {_fmt_yen(sr['range_52w_low'])}"],
        ["出来高(直近/20日平均)", f"{vol['latest']:,} / {vol['avg_20d']:,.0f}"],
    ]
    make_table(ax3, headers, rows, col_w=[0.5, 0.5], fs=9.0, row_scale=1.7)

    return fig


def build_pdf(code: str, info: dict, history, fundamentals: dict, valuation: dict, technical: dict, out_path: str):
    _reset_page_num()
    company_name = info.get("longName") or code
    footer_label = _footer_label(company_name, code)

    pages = [
        page_cover(footer_label, code, info, fundamentals, valuation, technical),
        page_fundamentals(footer_label, fundamentals),
        page_valuation(footer_label, valuation),
        page_technical(footer_label, history, technical),
    ]

    a4w, a4h = int(297 * 150 / 25.4), int(210 * 150 / 25.4)
    imgs = []
    for fig in pages:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        imgs.append(Image.open(buf).convert("RGB").resize((a4w, a4h), Image.LANCZOS))
        plt.close(fig)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    imgs[0].save(out_path, save_all=True, append_images=imgs[1:], resolution=150)
    return out_path
