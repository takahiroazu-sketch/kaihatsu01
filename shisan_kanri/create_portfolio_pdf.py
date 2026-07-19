#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ─── フォント設定 ───────────────────────────────────────────────────────────
import matplotlib.font_manager as fm
available = [f.name for f in fm.fontManager.ttflist]
JP_FONT = next(
    (f for f in ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Hiragino Kaku Gothic ProN',
                 'Yu Gothic', 'Noto Sans CJK JP', 'IPAexGothic']
     if f in available), None)
if JP_FONT:
    plt.rcParams['font.family'] = JP_FONT
plt.rcParams['axes.unicode_minus'] = False

# ─── カラー ─────────────────────────────────────────────────────────────────
NAVY   = '#1E3A5F'
BLUE   = '#2E86C1'
LIGHT  = '#D6EAF8'
GREEN  = '#1E8B4C'
RED    = '#C0392B'
GRAY   = '#585858'
WHITE  = '#FFFFFF'
GOLD   = '#F39C12'
PURPLE = '#8E44AD'
ORANGE = '#E67E22'
BG     = '#F8FBFF'

PIE_JP    = ['#2E86C1','#1E8B4C','#E67E22','#8E44AD','#C0392B','#17A589']
PIE_ASSET = ['#2E86C1','#1E8B4C','#E67E22','#8E44AD','#17A589']

# ─── データ ──────────────────────────────────────────────────────────────────
jp_tokutei = [
    ("ＪＡＣリク",      1804120,  833160),
    ("三井物産",        2037312, 1437264),
    ("三菱商事(特)",     699160,  353892),
    ("武田薬品",        1085480,  258720),
    ("蔵王産業",        1404089,  469362),
    ("ＮＴＴ(特)",     1202130,  186480),
    ("ＫＤＤＩ",        576958,  213166),
    ("オリックス",     1068925,  716898),
    ("三菱ＵＦＪ",      616264,  500832),
    ("Ｅギャランティ(特)", 503700,  99300),
    ("三井住友",         252798,  200109),
    ("ジャックス",       352000,   83700),
    ("東京海上",         129492,   97056),
    ("第一ライフ",       116128,   83104),
    ("ＣＤＳ",          583416,   49950),
    ("バルカー",         128960,   95552),
    ("伊藤忠",           193987,  122902),
    ("三菱ＨＣ",          28864,   13904),
    ("アサンテ",          53770,  -16036),
    ("アビスト",          39960,    3516),
    ("沖縄セルラー",      29200,   18816),
    ("ＪＲ九州",          27480,    5992),
]
jp_nisa_growth = [
    ("キヤノン",        431000,  -56300),
    ("三菱商事(NISA)",  454000,  193900),
    ("Ｅギャランティ(N)", 335800,  78600),
    ("ＮＴＴ(NISA)",   505400,  -89600),
]
jp_old_nisa = [("信越化学",  731000, 302700)]

jp_stock_total  = 12934193.5 + 1726200 + 731000
jp_stock_profit = 5827639.5  + 126600  + 302700
jp_stock_cost   = jp_stock_total - jp_stock_profit

jp_funds = [
    ("eMAXIS Slim\nオールカントリー\n（成長投資枠）", 4253472, 1140708, 3112764),
    ("eMAXIS Slim\nオールカントリー\n（つみたて枠）",  3362294, 1062254, 2300040),
]
jp_fund_total  = 4253472 + 3362294
jp_fund_profit = 1140708 + 1062254

us_tokutei = [
    ("VTI\nバンガードTSM",    180, 211.55, 369.99, 10749615, 6510795),
    ("HDV\n高配当ETF",        750,  19.42,  26.99,  3267341, 1646591),
    ("SPYD\nS&P500高配当",    100,  40.32,  47.50,   766697,  317997),
    ("AMBQ\nアンビック",       80,  34.98,  90.48,  1168350,  752830),
]
us_nisa = [
    ("HDV\n高配当(NISA)",     440,  21.86,  26.99,  1916840,  494760),
    ("PLTR\nパランティア",      7,  72.00, 128.47,   145154,   68112),
]
us_old_nisa = [
    ("SKYT\nスカイウォーター", 450,  5.39,  36.57,  2656243, 2293993),
]
us_tokutei_total  = 15952003;  us_tokutei_profit = 9228213
us_nisa_total     = 2061994;   us_nisa_profit    = 562872
us_old_nisa_total = 2656243;   us_old_nisa_profit = 2293993
us_stock_total    = us_tokutei_total + us_nisa_total + us_old_nisa_total
us_stock_profit   = us_tokutei_profit + us_nisa_profit + us_old_nisa_profit

us_bonds = [
    ("4.125% 2027/9満期",  12717.44, 2052721),
    ("4.750% 2053/11満期", 13178.10, 2127077),
    ("4.250% 2035/8満期",   3900.00,  629499),
    ("4.000% 2035/11満期", 14626.28, 2360827),
]
us_bond_total = 7170124

# ── SBI証券 預り金 ──
sbi_usd_cash   = 1_880_000   # 米ドル188万円相当
sbi_jpy_cash   = 1_200_000   # 円120万円
SBI_CASH_TOTAL = sbi_usd_cash + sbi_jpy_cash   # 3,080,000

GRAND_TOTAL  = jp_stock_total + jp_fund_total + us_stock_total + us_bond_total + SBI_CASH_TOTAL
GRAND_PROFIT = jp_stock_profit + jp_fund_profit + us_stock_profit

# ─── ヘルパー関数 ────────────────────────────────────────────────────────────

def new_fig(title="", subtitle=""):
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=BG)  # A4横
    fig.patch.set_facecolor(BG)

    if title:
        # ヘッダーバー
        ax_h = fig.add_axes([0, 0.88, 1, 0.12])
        ax_h.set_facecolor(NAVY)
        ax_h.set_xlim(0, 1); ax_h.set_ylim(0, 1)
        ax_h.axis('off')
        ax_h.text(0.02, 0.65, title, color=WHITE, fontsize=20, fontweight='bold',
                  va='center', transform=ax_h.transAxes)
        if subtitle:
            ax_h.text(0.02, 0.18, subtitle, color='#AACCEE', fontsize=9,
                      va='center', transform=ax_h.transAxes)
        # 下部の細いアクセントライン
        ax_h.axhline(0, color=GOLD, linewidth=3)

    return fig


def add_kpi_boxes(fig, kpis, y=0.73, h=0.12):
    n = len(kpis)
    w = 0.88 / n
    for i, (label, value, color) in enumerate(kpis):
        x = 0.06 + i * w
        ax = fig.add_axes([x, y, w - 0.01, h])
        ax.set_facecolor(WHITE)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
        for spine in ax.spines.values():
            spine.set_visible(False)
        rect = FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02",
                              linewidth=1.5, edgecolor=BLUE, facecolor=WHITE)
        ax.add_patch(rect)
        ax.text(0.5, 0.72, label, ha='center', va='center', fontsize=8, color=GRAY)
        ax.text(0.5, 0.32, value, ha='center', va='center', fontsize=13,
                fontweight='bold', color=color)


# ─── スライド 1: 表紙 ────────────────────────────────────────────────────────

def slide_cover():
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=NAVY)
    fig.patch.set_facecolor(NAVY)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(NAVY); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # ゴールドライン
    ax.axhline(0.44, color=GOLD, linewidth=4, xmin=0.05, xmax=0.95)

    # タイトル
    ax.text(0.5, 0.75, "保有証券 ポートフォリオ分析", ha='center', va='center',
            color=WHITE, fontsize=28, fontweight='bold')
    ax.text(0.5, 0.62, "レポート", ha='center', va='center',
            color=GOLD, fontsize=22, fontweight='bold')
    ax.text(0.5, 0.50, "2026年6月19日 時点", ha='center', va='center',
            color='#AACCEE', fontsize=13)

    # KPI 4つ
    kpi_data = [
        ("総資産評価額",    f"約 {GRAND_TOTAL/1e8:.2f} 億円"),
        ("総評価益",        f"+{GRAND_PROFIT/1e4:.0f} 万円"),
        ("損益率",          f"+{GRAND_PROFIT/(GRAND_TOTAL-GRAND_PROFIT-SBI_CASH_TOTAL)*100:.1f}%"),
        ("保有銘柄数",      "日本28 ＋ 米国7"),
    ]
    for i, (lbl, val) in enumerate(kpi_data):
        x = 0.08 + i * 0.22
        rect = FancyBboxPatch((x, 0.20), 0.20, 0.16,
                              boxstyle="round,pad=0.01", linewidth=1.5,
                              edgecolor=GOLD, facecolor='#2A4A70',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x + 0.10, 0.33, lbl, ha='center', va='center',
                color='#AACCEE', fontsize=8, transform=ax.transAxes)
        ax.text(x + 0.10, 0.24, val, ha='center', va='center',
                color=GOLD, fontsize=11, fontweight='bold', transform=ax.transAxes)

    ax.text(0.5, 0.10, "日本株 ・ 米国株 ・ 投資信託 ・ 米国国債",
            ha='center', color='#6699BB', fontsize=11)
    return fig


# ─── スライド 2: ポートフォリオ全体概要 ──────────────────────────────────────

def slide_overview():
    fig = new_fig("ポートフォリオ全体概要",
                  f"総評価額: {GRAND_TOTAL/1e8:.2f}億円  ｜  総評価益: +{GRAND_PROFIT/1e4:.0f}万円  ｜  2026年6月19日")

    kpis = [
        ("日本株合計",   f"{jp_stock_total/1e4:.0f}万円",   GREEN),
        ("日本投資信託", f"{jp_fund_total/1e4:.0f}万円",    GREEN),
        ("米国株合計",   f"{us_stock_total/1e4:.0f}万円",   ORANGE),
        ("米国国債",     f"{us_bond_total/1e4:.0f}万円",    PURPLE),
    ]
    add_kpi_boxes(fig, kpis, y=0.73, h=0.13)

    # 左: アセット配分円グラフ
    ax1 = fig.add_axes([0.03, 0.05, 0.42, 0.65])
    labels = ['日本株\n（特定・NISA）', '日本\n投資信託', '米国株\n（特定・NISA）', '米国\n国債', 'SBI\n預り金']
    sizes  = [jp_stock_total, jp_fund_total, us_stock_total, us_bond_total, SBI_CASH_TOTAL]
    wedges, texts, autotexts = ax1.pie(
        sizes, labels=labels, colors=PIE_ASSET,
        autopct='%1.1f%%', startangle=140,
        textprops={'fontsize': 9.5},
        wedgeprops={'linewidth': 2, 'edgecolor': 'white'},
        explode=[0.03]*5
    )
    for at in autotexts:
        at.set_fontsize(9); at.set_fontweight('bold'); at.set_color(WHITE)
    ax1.set_title('アセット配分', fontsize=13, fontweight='bold', pad=8)

    # 右: 口座別棒グラフ
    ax2 = fig.add_axes([0.50, 0.10, 0.48, 0.60])
    bar_labels = ['日本株\n特定', '日本株\nNISA成長', '日本株\n旧NISA',
                  '投信\nNISA成長', '投信\nつみたて',
                  '米国株\n特定', '米国株\nNISA', '米国株\n旧NISA', '米国\n国債', 'SBI\n預り金']
    bar_vals = [jp_stock_total - 1726200 - 731000, 1726200, 731000,
                4253472, 3362294,
                us_tokutei_total, us_nisa_total, us_old_nisa_total, us_bond_total, SBI_CASH_TOTAL]
    bcolors  = ['#2E86C1','#5DADE2','#85C1E9',
                '#1E8B4C','#52BE80',
                '#E67E22','#F0A500','#D4AC0D','#8E44AD','#17A589']
    bars = ax2.bar(range(len(bar_labels)), [v/1e6 for v in bar_vals],
                   color=bcolors, edgecolor='white', linewidth=1.2, width=0.7)
    ax2.set_xticks(range(len(bar_labels)))
    ax2.set_xticklabels(bar_labels, fontsize=7.5)
    ax2.set_ylabel('評価額（百万円）', fontsize=9)
    ax2.set_title('口座別 評価額', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.35); ax2.spines[['top','right']].set_visible(False)
    for bar, val in zip(bars, bar_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.08,
                 f'{val/1e6:.1f}M', ha='center', fontsize=7, fontweight='bold')
    return fig


# ─── スライド 3: 日本株 評価額ランキング ──────────────────────────────────────

def slide_jp_ranking():
    fig = new_fig("日本株 保有銘柄 評価額ランキング",
                  f"特定22銘柄 ＋ NISA4銘柄 ＋ 旧NISA1銘柄  ｜  合計 {jp_stock_total/1e4:.0f}万円  ｜  損益 +{jp_stock_profit/1e4:.0f}万円")

    all_stocks = jp_tokutei + jp_nisa_growth + jp_old_nisa
    sorted_s = sorted(all_stocks, key=lambda x: x[1], reverse=True)
    names = [s[0] for s in sorted_s]
    vals  = [s[1]/1e4 for s in sorted_s]
    profs = [s[2] for s in sorted_s]

    ax = fig.add_axes([0.04, 0.04, 0.62, 0.82])
    colors_bar = ['#2E86C1'] * len(names)
    bars = ax.barh(range(len(names)), vals, color=colors_bar,
                   edgecolor='white', linewidth=0.8, height=0.72)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8.5)
    ax.set_xlabel('評価額（万円）', fontsize=9)
    ax.set_title('全銘柄 評価額（万円）', fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.35); ax.spines[['top','right']].set_visible(False)

    for i, (bar, val, prof) in enumerate(zip(bars, vals, profs)):
        sign  = '+' if prof >= 0 else ''
        pcolor = GREEN if prof >= 0 else RED
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f'{val:.0f}万  {sign}{prof/1e4:.1f}万',
                va='center', fontsize=7.5, color=pcolor)
    ax.set_xlim(0, max(vals) * 1.45)

    # 右側に損益ランキング
    ax2 = fig.add_axes([0.70, 0.04, 0.28, 0.82])
    sorted_p = sorted(all_stocks, key=lambda x: x[2], reverse=True)
    pnames = [s[0] for s in sorted_p[:15]]
    pvals  = [s[2]/1e4 for s in sorted_p[:15]]
    pcolors = [GREEN if v >= 0 else RED for v in pvals]
    bars2 = ax2.barh(range(len(pnames)), pvals, color=pcolors,
                     edgecolor='white', linewidth=0.8, height=0.72)
    ax2.set_yticks(range(len(pnames)))
    ax2.set_yticklabels(pnames, fontsize=8)
    ax2.set_xlabel('損益（万円）', fontsize=9)
    ax2.set_title('損益 上位15銘柄', fontsize=11, fontweight='bold')
    ax2.invert_yaxis()
    ax2.grid(axis='x', alpha=0.35); ax2.spines[['top','right']].set_visible(False)
    ax2.axvline(0, color=GRAY, linewidth=0.8)
    return fig


# ─── スライド 4: 日本株 セクター分析 ─────────────────────────────────────────

def slide_jp_sector():
    fig = new_fig("日本株 セクター別分析",
                  "特定預り・NISA成長投資枠・旧NISA 合算  ｜  金融・商社・通信が主力3セクター")

    sectors = {
        '金融':       616264 + 252798 + 352000 + 1068925 + 28864 + 116128 + 129492 + 503700 + 335800,
        '商社':       2037312 + 699160 + 454000 + 193987,
        '通信':       1202130 + 505400 + 576958 + 29200,
        '化学・素材': 1085480 + 731000,
        '人材・ｻｰﾋﾞｽ': 1804120 + 53770 + 39960 + 27480,
        'その他':     583416 + 128960 + 1404089 + 431000,
    }

    ax_pie = fig.add_axes([0.04, 0.08, 0.44, 0.72])
    wedges, texts, autotexts = ax_pie.pie(
        list(sectors.values()), labels=list(sectors.keys()),
        colors=PIE_JP, autopct='%1.1f%%', startangle=100,
        textprops={'fontsize': 10.5},
        wedgeprops={'linewidth': 2, 'edgecolor': 'white'},
        explode=[0.04]*len(sectors)
    )
    for at in autotexts:
        at.set_fontsize(9.5); at.set_fontweight('bold')
    ax_pie.set_title('セクター構成', fontsize=13, fontweight='bold', pad=8)

    # 右: セクター別棒グラフ
    ax_bar = fig.add_axes([0.52, 0.12, 0.44, 0.65])
    sec_names = list(sectors.keys())
    sec_vals  = [v/1e4 for v in sectors.values()]
    bars = ax_bar.barh(range(len(sec_names)), sec_vals,
                       color=PIE_JP, edgecolor='white', linewidth=1.2, height=0.6)
    ax_bar.set_yticks(range(len(sec_names)))
    ax_bar.set_yticklabels(sec_names, fontsize=10.5)
    ax_bar.set_xlabel('評価額（万円）', fontsize=9)
    ax_bar.set_title('セクター別 評価額', fontsize=12, fontweight='bold')
    ax_bar.invert_yaxis()
    ax_bar.grid(axis='x', alpha=0.35); ax_bar.spines[['top','right']].set_visible(False)
    for bar, val in zip(bars, sec_vals):
        ax_bar.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                    f'{val:.0f}万', va='center', fontsize=9, fontweight='bold')
    ax_bar.set_xlim(0, max(sec_vals) * 1.22)
    return fig


# ─── スライド 5: 日本株 NISA口座詳細 ────────────────────────────────────────

def slide_jp_nisa():
    fig = new_fig("日本株 NISA口座 保有状況",
                  f"NISA成長投資枠 4銘柄（172.6万円 ｜ +12.7万）  ｜  旧NISA 1銘柄（73.1万円 ｜ +30.3万）")

    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    headers = ["銘柄", "口座種別", "保有\n株数", "取得\n単価(円)", "現在値\n(円)", "評価額\n(円)", "評価損益\n(円)"]
    rows = [
        ("キヤノン",         "NISA成長投資枠", "100",   "4,873",   "4,310",   "431,000", "▲56,300",  False),
        ("三菱商事",         "NISA成長投資枠", "100",   "2,601",   "4,540",   "454,000", "+193,900", True),
        ("Eギャランティ",    "NISA成長投資枠", "200",   "1,286",   "1,679",   "335,800", "+78,600",  True),
        ("NTT",              "NISA成長投資枠", "3,500", "170",     "144",     "505,400", "▲89,600",  False),
        ("信越化学",         "旧NISA",         "100",   "4,283",   "7,310",   "731,000", "+302,700", True),
    ]

    col_xs = [0.03, 0.18, 0.33, 0.43, 0.53, 0.63, 0.76]
    col_ws = [0.14, 0.14, 0.09, 0.09, 0.09, 0.12, 0.21]

    # ヘッダー
    hy = 0.76
    for hdr, cx, cw in zip(headers, col_xs, col_ws):
        rect = FancyBboxPatch((cx, hy), cw-0.005, 0.065,
                              boxstyle="round,pad=0.003",
                              linewidth=0, facecolor=NAVY,
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(cx + cw/2, hy + 0.033, hdr, ha='center', va='center',
                color=WHITE, fontsize=8.5, fontweight='bold',
                transform=ax.transAxes)

    # データ行
    for i, row in enumerate(rows):
        vals, is_pos = row[:-1], row[-1]
        bg = '#EEF5FF' if i % 2 == 0 else WHITE
        ry = 0.69 - i * 0.085
        for j, (val, cx, cw) in enumerate(zip(vals, col_xs, col_ws)):
            rect = FancyBboxPatch((cx, ry), cw-0.005, 0.078,
                                  boxstyle="round,pad=0.002",
                                  linewidth=0.5, edgecolor='#CCDDEE',
                                  facecolor=bg, transform=ax.transAxes)
            ax.add_patch(rect)
            if j == 6:  # 損益列
                color = GREEN if '+' in str(val) else RED
                fw = 'bold'
            else:
                color = NAVY; fw = 'normal'
            ax.text(cx + cw/2, ry + 0.039, val, ha='center', va='center',
                    color=color, fontsize=9, fontweight=fw,
                    transform=ax.transAxes)

    # 合計行
    ry_sum = 0.69 - len(rows) * 0.085
    totals = ["合計", "", "", "", "", "1,926,200", "+429,300"]
    for j, (val, cx, cw) in enumerate(zip(totals, col_xs, col_ws)):
        rect = FancyBboxPatch((cx, ry_sum), cw-0.005, 0.078,
                              boxstyle="round,pad=0.002",
                              linewidth=1.5, edgecolor=BLUE,
                              facecolor=LIGHT, transform=ax.transAxes)
        ax.add_patch(rect)
        color = GREEN if '+' in str(val) else NAVY
        ax.text(cx + cw/2, ry_sum + 0.039, val, ha='center', va='center',
                color=color, fontsize=10, fontweight='bold',
                transform=ax.transAxes)

    # ポイント解説
    points = [
        ("✓ NTT・キヤノン",  "若干の含み損。配当利回り目的で継続保有"),
        ("✓ 三菱商事",        "NISA口座で+19.4万円。資源価格上昇の恩恵"),
        ("✓ 信越化学（旧NISA）", "+73.1%の大幅上昇。半導体材料の需要増"),
    ]
    for i, (title, desc) in enumerate(points):
        yx = 0.14 - i * 0.065
        ax.text(0.03, yx, title, color=BLUE, fontsize=10, fontweight='bold',
                transform=ax.transAxes)
        ax.text(0.28, yx, desc, color=GRAY, fontsize=9,
                transform=ax.transAxes)
    return fig


# ─── スライド 6: 日本 投資信託 ───────────────────────────────────────────────

def slide_jp_fund():
    fig = new_fig("日本 投資信託（eMAXIS Slim オールカントリー）",
                  f"NISA成長投資枠 ＋ つみたて投資枠  ｜  合計評価額 {jp_fund_total/1e4:.0f}万円  ｜  評価益 +{jp_fund_profit/1e4:.0f}万円")

    # 2口座の円グラフ
    for i, (name, val, profit, cost) in enumerate(jp_funds):
        ax = fig.add_axes([0.04 + i * 0.44, 0.12, 0.38, 0.60])
        slices = [cost, profit]
        clrs   = [BLUE, GREEN]
        wedges, texts, autotexts = ax.pie(
            slices, colors=clrs, autopct='%1.1f%%', startangle=90,
            wedgeprops={'linewidth': 2, 'edgecolor': 'white'},
            textprops={'fontsize': 10}
        )
        for at in autotexts:
            at.set_fontsize(10); at.set_fontweight('bold')
        short = name.replace('\n', ' ')
        rate = profit / cost * 100
        ax.set_title(f'{short}\n評価額: {val/1e4:.0f}万円  (+{rate:.1f}%)',
                     fontsize=10.5, fontweight='bold', pad=6)

    # 凡例
    ax_l = fig.add_axes([0.35, 0.02, 0.30, 0.10])
    ax_l.axis('off')
    patches_l = [mpatches.Patch(color=BLUE,  label='取得金額'),
                 mpatches.Patch(color=GREEN, label='評価益')]
    ax_l.legend(handles=patches_l, loc='center', ncol=2, fontsize=11)

    # 右側の情報テーブル
    ax_t = fig.add_axes([0.88, 0.10, 0.10, 0.75])
    ax_t.axis('off')
    info = [
        ("ファンド",   "eMAXIS Slim\n全世界株式\n（オール・カントリー）"),
        ("運用会社",   "三菱UFJ\nアセットマネジメント"),
        ("成長投資枠", "取得: 311.3万\n評価: 425.3万\n+36.6%"),
        ("つみたて枠", "取得: 230.0万\n評価: 336.2万\n+46.2%"),
        ("合計",       f"取得: {(jp_fund_total-jp_fund_profit)/1e4:.0f}万\n評価: {jp_fund_total/1e4:.0f}万\n+{jp_fund_profit/(jp_fund_total-jp_fund_profit)*100:.1f}%"),
        ("分配金",     "再投資型"),
    ]
    for i, (k, v) in enumerate(info):
        ax_t.text(0.5, 0.95 - i*0.165, k, ha='center', fontsize=8,
                  fontweight='bold', color=NAVY, transform=ax_t.transAxes)
        ax_t.text(0.5, 0.87 - i*0.165, v, ha='center', fontsize=7.5,
                  color=GRAY, transform=ax_t.transAxes)
    return fig


# ─── スライド 7: 米国株 ──────────────────────────────────────────────────────

def slide_us_stock():
    fig = new_fig("米国株式 保有状況",
                  f"特定4銘柄 ＋ NISA2銘柄 ＋ 旧NISA1銘柄  ｜  円換算合計 {us_stock_total/1e4:.0f}万円  ｜  評価益 +{us_stock_profit/1e4:.0f}万円")

    all_us = us_tokutei + us_nisa + us_old_nisa
    names  = [s[0].replace('\n', '\n') for s in all_us]
    vals   = [s[4]/1e6 for s in all_us]
    profs  = [s[5] for s in all_us]
    colors = [ORANGE]*4 + ['#F0A500']*2 + ['#D4AC0D']

    ax1 = fig.add_axes([0.04, 0.12, 0.55, 0.65])
    bars = ax1.bar(range(len(names)), vals, color=colors,
                   edgecolor='white', linewidth=1.2, width=0.7)
    ax1.set_xticks(range(len(names)))
    ax1.set_xticklabels([n.split('\n')[0] for n in names], fontsize=10)
    ax1.set_ylabel('円換算評価額（百万円）', fontsize=9)
    ax1.set_title('銘柄別 評価額（円換算）', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.35); ax1.spines[['top','right']].set_visible(False)
    for bar, val, prof in zip(bars, vals, profs):
        sign = '+' if prof >= 0 else ''
        pcol = GREEN if prof >= 0 else RED
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f'{val:.1f}M\n{sign}{prof/1e4:.0f}万',
                 ha='center', fontsize=8.5, fontweight='bold', color=pcol)
    patches_l = [mpatches.Patch(color=ORANGE,   label='特定預り'),
                 mpatches.Patch(color='#F0A500', label='NISA'),
                 mpatches.Patch(color='#D4AC0D', label='旧NISA')]
    ax1.legend(handles=patches_l, fontsize=9)

    # 右側: 損益率バーチャート
    ax2 = fig.add_axes([0.64, 0.12, 0.33, 0.65])
    rates = [(s[4]-s[5])>0 and s[5]/(s[4]-s[5])*100 for s in all_us]
    names_short = [s[0].split('\n')[0] for s in all_us]
    bar_colors2 = [GREEN if r > 0 else RED for r in rates]
    ax2.barh(range(len(names_short)), rates, color=bar_colors2,
             edgecolor='white', linewidth=0.8, height=0.65)
    ax2.set_yticks(range(len(names_short)))
    ax2.set_yticklabels(names_short, fontsize=9.5)
    ax2.set_xlabel('損益率（%）', fontsize=9)
    ax2.set_title('銘柄別 損益率', fontsize=12, fontweight='bold')
    ax2.invert_yaxis()
    ax2.axvline(0, color=GRAY, linewidth=0.8)
    ax2.grid(axis='x', alpha=0.35); ax2.spines[['top','right']].set_visible(False)
    for i, (rate, bar) in enumerate(zip(rates, ax2.patches)):
        sign = '+' if rate > 0 else ''
        ax2.text(max(rate + 5, 5), bar.get_y() + bar.get_height()/2,
                 f'{sign}{rate:.0f}%', va='center', fontsize=9, fontweight='bold',
                 color=GREEN if rate > 0 else RED)
    return fig


# ─── スライド 8: 米国債券 ────────────────────────────────────────────────────

def slide_us_bond():
    fig = new_fig("米ドル建て国債 保有状況",
                  f"特定預り 4本  ｜  円換算合計 {us_bond_total/1e4:.0f}万円  ｜  為替レート 約157〜161円/USD")

    bond_names  = [b[0] for b in us_bonds]
    bond_usd    = [b[1] for b in us_bonds]
    bond_jpy    = [b[2] for b in us_bonds]

    # 左: 棒グラフ
    ax1 = fig.add_axes([0.04, 0.14, 0.44, 0.62])
    bars = ax1.bar(range(4), [j/1e4 for j in bond_jpy],
                  color=['#8E44AD','#9B59B6','#A569BD','#BB8FCE'],
                  edgecolor='white', linewidth=1.2, width=0.6)
    ax1.set_xticks(range(4))
    ax1.set_xticklabels(['2027\n満期','2053\n満期','2035(8月)\n満期','2035(11月)\n満期'], fontsize=9)
    ax1.set_ylabel('円換算評価額（万円）', fontsize=9)
    ax1.set_title('満期別 評価額（円換算）', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.35); ax1.spines[['top','right']].set_visible(False)
    for bar, jpy, usd in zip(bars, bond_jpy, bond_usd):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                 f'{jpy/1e4:.0f}万\n(${usd:,.0f})',
                 ha='center', fontsize=8, fontweight='bold')

    # 右: 構成比円グラフ
    ax2 = fig.add_axes([0.52, 0.14, 0.44, 0.62])
    wedges, texts, autotexts = ax2.pie(
        bond_jpy,
        labels=['2027\n満期','2053\n満期','2035(8月)','2035(11月)'],
        colors=['#8E44AD','#9B59B6','#A569BD','#BB8FCE'],
        autopct='%1.1f%%', startangle=90,
        textprops={'fontsize': 10},
        wedgeprops={'linewidth': 2, 'edgecolor': 'white'},
        explode=[0.03]*4
    )
    for at in autotexts:
        at.set_fontsize(9.5); at.set_fontweight('bold')
    ax2.set_title('満期別 構成比', fontsize=12, fontweight='bold', pad=8)

    # 下部テーブル
    ax_t = fig.add_axes([0.03, 0.02, 0.94, 0.10])
    ax_t.axis('off'); ax_t.set_xlim(0, 1); ax_t.set_ylim(0, 1)
    note_rows = [
        "【短期債】2027年満期：USD12,400 / 利率4.125% / 円換算205.3万円",
        "【中期債】2035年8月：USD3,900 / 利率4.250% / 円換算62.9万円   2035年11月：USD14,600 / 利率4.000% / 円換算236.1万円",
        "【超長期債】2053年満期：USD13,000 / 利率4.750% / 円換算212.7万円  ※満期分散で金利リスクを管理",
    ]
    for i, note in enumerate(note_rows):
        ax_t.text(0.02, 0.85 - i * 0.32, note, fontsize=7.5, color=GRAY,
                  transform=ax_t.transAxes)
    return fig


# ─── スライド 9: 運用成績まとめ ──────────────────────────────────────────────

def slide_performance():
    fig = new_fig("運用成績まとめ",
                  f"総評価額 {GRAND_TOTAL/1e8:.2f}億円  ｜  総評価益 +{GRAND_PROFIT/1e4:.0f}万円  ｜  損益率 +{GRAND_PROFIT/(GRAND_TOTAL-GRAND_PROFIT-SBI_CASH_TOTAL)*100:.1f}%（投資部分）")

    categories = ['日本株\n（特定・NISA）', '日本\n投資信託', '米国株\n（全口座）']
    costs   = [jp_stock_cost, jp_fund_total - jp_fund_profit, us_stock_total - us_stock_profit]
    profits = [jp_stock_profit, jp_fund_profit, us_stock_profit]
    rates   = [p/c*100 for p, c in zip(profits, costs)]

    ax1 = fig.add_axes([0.05, 0.12, 0.55, 0.68])
    x = np.arange(len(categories))
    w = 0.55
    b1 = ax1.bar(x, [c/1e6 for c in costs], width=w, label='取得金額', color=BLUE, edgecolor='white')
    b2 = ax1.bar(x, [p/1e6 for p in profits], width=w, bottom=[c/1e6 for c in costs],
                 label='評価益', color=GREEN, edgecolor='white')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=11)
    ax1.set_ylabel('金額（百万円）', fontsize=10)
    ax1.set_title('取得金額 vs 評価益（積み上げ）', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.35); ax1.spines[['top','right']].set_visible(False)
    ax1.legend(fontsize=10)
    for bar, p, c in zip(b2, profits, costs):
        rate = p / c * 100
        ax1.text(bar.get_x() + bar.get_width()/2,
                 (c + p)/1e6 + 0.3,
                 f'+{rate:.0f}%', ha='center', fontsize=11.5,
                 fontweight='bold', color=GREEN)

    # 右: カード
    summary = [
        ("日本株（特定+NISA）", f"{jp_stock_total/1e4:.0f}万円",
         f"+{jp_stock_profit/1e4:.0f}万円", GREEN,
         f"損益率 +{jp_stock_profit/jp_stock_cost*100:.0f}%"),
        ("日本 投資信託", f"{jp_fund_total/1e4:.0f}万円",
         f"+{jp_fund_profit/1e4:.0f}万円", GREEN,
         f"損益率 +{jp_fund_profit/(jp_fund_total-jp_fund_profit)*100:.0f}%"),
        ("米国株（全口座）", f"{us_stock_total/1e4:.0f}万円",
         f"+{us_stock_profit/1e4:.0f}万円", GREEN,
         f"損益率 +{us_stock_profit/(us_stock_total-us_stock_profit)*100:.0f}%"),
        ("米国国債", f"{us_bond_total/1e4:.0f}万円",
         "—", PURPLE, "安定運用"),
        ("SBI預り金\n（USD+円）", f"{SBI_CASH_TOTAL/1e4:.0f}万円",
         "—", '#17A589', "USD188万＋円120万"),
    ]

    ax_c = fig.add_axes([0.63, 0.08, 0.35, 0.82])
    ax_c.axis('off'); ax_c.set_xlim(0, 1); ax_c.set_ylim(0, 1)

    for i, (label, total, profit, pcolor, rate) in enumerate(summary):
        y_base = 0.78 - i * 0.185
        rect = FancyBboxPatch((0.02, y_base), 0.96, 0.165,
                              boxstyle="round,pad=0.02",
                              linewidth=1.5, edgecolor=pcolor,
                              facecolor='#F5F9FF', transform=ax_c.transAxes)
        ax_c.add_patch(rect)
        ax_c.text(0.5, y_base + 0.12, label, ha='center', fontsize=10,
                  fontweight='bold', color=NAVY, transform=ax_c.transAxes)
        ax_c.text(0.25, y_base + 0.05, f'評価額: {total}', ha='center', fontsize=9,
                  color=GRAY, transform=ax_c.transAxes)
        ax_c.text(0.75, y_base + 0.05, f'損益: {profit} ({rate})', ha='center',
                  fontsize=9, fontweight='bold', color=pcolor, transform=ax_c.transAxes)

    # 総合計
    rect_t = FancyBboxPatch((0.02, 0.02), 0.96, 0.10,
                            boxstyle="round,pad=0.02",
                            linewidth=2, edgecolor=GOLD,
                            facecolor=NAVY, transform=ax_c.transAxes)
    ax_c.add_patch(rect_t)
    ax_c.text(0.5, 0.093, f"合計: {GRAND_TOTAL/1e8:.2f}億円", ha='center',
              fontsize=11, fontweight='bold', color=WHITE, transform=ax_c.transAxes)
    ax_c.text(0.5, 0.030, f"総評価益: +{GRAND_PROFIT/1e4:.0f}万円  (+{GRAND_PROFIT/(GRAND_TOTAL-GRAND_PROFIT-SBI_CASH_TOTAL)*100:.1f}%・投資部分)",
              ha='center', fontsize=10, fontweight='bold', color=GOLD, transform=ax_c.transAxes)
    return fig


# ─── スライド 10: ポートフォリオの特徴 ────────────────────────────────────────

def slide_features():
    fig = new_fig("ポートフォリオの特徴と注目銘柄")

    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    features = [
        ("分散投資",      BLUE,
         "日本株28銘柄 ＋ 米国株7銘柄 ＋ 投信 ＋ 国債の\n4資産に分散。地域・セクター・商品タイプを幅広くカバー。"),
        ("高配当重視",    GREEN,
         "NTT・KDDI・オリックス・三菱商事など高配当株が中核。\n米国はHDV・SPYDの高配当ETFでインカムゲインを確保。"),
        ("成長株保有",    ORANGE,
         "SKYT（+578%）・PLTR（+78%）など米国ハイテク成長株を\nNISA口座で非課税保有。国内はJAC・三井物産も大幅高。"),
        ("NISA最大活用",  PURPLE,
         "成長投資枠・つみたて投資枠・旧NISAをフル活用。\n非課税口座での利益最大化を実現。"),
        ("債券でリスク管理", RED,
         "米国国債4本（2027〜2053年）を保有。短中長期の\n満期分散でポートフォリオの安定性を確保。"),
    ]

    positions = [(0.03, 0.56), (0.52, 0.56), (0.03, 0.22), (0.52, 0.22), (0.275, -0.12)]
    for i, ((title, color, desc), (xb, yb)) in enumerate(zip(features, positions)):
        rect = FancyBboxPatch((xb, yb + 0.05), 0.44, 0.28,
                              boxstyle="round,pad=0.015",
                              linewidth=2, edgecolor=color,
                              facecolor=color + '18' if len(color) == 7 else '#F0F8FF',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(xb + 0.03, yb + 0.28, f"● {title}", fontsize=12,
                fontweight='bold', color=color, transform=ax.transAxes)
        ax.text(xb + 0.03, yb + 0.17, desc, fontsize=9, color=GRAY,
                transform=ax.transAxes, linespacing=1.5)

    # 注目銘柄ピックアップ
    ax2 = fig.add_axes([0.02, 0.02, 0.96, 0.085])
    ax2.set_facecolor('#F0F4FF')
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0.5, 0.75, "注目銘柄 ｜ SKYT +578%  ・  三井物産 +239%  ・  三菱UFJ +82%  ・  VTI +75%  ・  PLTR +78%  ・  信越化学 +71%",
             ha='center', va='center', fontsize=9.5, color=NAVY, fontweight='bold',
             transform=ax2.transAxes)
    return fig


# ─── PDF出力 ─────────────────────────────────────────────────────────────────

output_path = "/Users/takahiroazuma/Desktop/kabu/claude/portfolio_report.pdf"

slides = [
    slide_cover,
    slide_overview,
    slide_jp_ranking,
    slide_jp_sector,
    slide_jp_nisa,
    slide_jp_fund,
    slide_us_stock,
    slide_us_bond,
    slide_performance,
    slide_features,
]

import os, io
from PIL import Image

print("PDFを生成中（PNG→PDF変換方式）...")
pil_images = []
for i, slide_fn in enumerate(slides):
    print(f"  スライド {i+1}/{len(slides)}: {slide_fn.__name__}")
    fig = slide_fn()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).convert('RGB')
    pil_images.append(img)
    plt.close(fig)

# A4横(297×210mm)にリサイズ
A4_W = int(297 * 150 / 25.4)
A4_H = int(210 * 150 / 25.4)
resized = []
for img in pil_images:
    img_r = img.resize((A4_W, A4_H), Image.LANCZOS)
    resized.append(img_r)

resized[0].save(
    output_path, save_all=True,
    append_images=resized[1:],
    resolution=150
)

size_kb = os.path.getsize(output_path) // 1024
print(f"\n✅ 保存完了: {output_path}")
print(f"   ファイルサイズ: {size_kb} KB")
print(f"   ページ数: {len(slides)}ページ")
