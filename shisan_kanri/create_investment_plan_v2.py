#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投資プラン提案 PDF v2
- SBI証券データ（data/260619jp.csv, data/260619us.csv）
- 楽天証券データ（data/assetbalance(all)_20260621_182239rakuten.csv）
- 現金900万円（SBI以外）を追加
- output/ フォルダに出力
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import warnings, io, os
from PIL import Image
warnings.filterwarnings('ignore')

# ─── フォント ─────────────────────────────────────────────────────────────────
import matplotlib.font_manager as fm
available = [f.name for f in fm.fontManager.ttflist]
JP_FONT = next(
    (f for f in ['Hiragino Sans','Hiragino Kaku Gothic ProN','Hiragino Kaku Gothic Pro',
                 'Yu Gothic','Noto Sans CJK JP','IPAexGothic'] if f in available), None)
if JP_FONT:
    plt.rcParams['font.family'] = JP_FONT
plt.rcParams['axes.unicode_minus'] = False

# ─── カラー ──────────────────────────────────────────────────────────────────
NAVY   = '#1E3A5F'; BLUE   = '#2E86C1'; LIGHT  = '#D6EAF8'
GREEN  = '#1E8B4C'; RED    = '#C0392B'; GRAY   = '#585858'
WHITE  = '#FFFFFF'; GOLD   = '#F39C12'; PURPLE = '#8E44AD'
ORANGE = '#E67E22'; TEAL   = '#17808B'; BG     = '#F8FBFF'
RAKUTEN= '#BF0000'  # 楽天カラー

# ─── ═══════ ポートフォリオデータ ═══════ ──────────────────────────────────────

# ── SBI証券 日本株 ──
jp_tokutei = [
    ("ＪＡＣリク",        1804120,  833160),
    ("三井物産",           2037312, 1437264),
    ("三菱商事(特)",        699160,  353892),
    ("武田薬品",           1085480,  258720),
    ("蔵王産業",           1404089,  469362),
    ("ＮＴＴ(特)",        1202130,  186480),
    ("ＫＤＤＩ",           576958,  213166),
    ("オリックス",        1068925,  716898),
    ("三菱ＵＦＪ",         616264,  500832),
    ("Ｅギャランティ(特)", 503700,   99300),
    ("三井住友",            252798,  200109),
    ("ジャックス",          352000,   83700),
    ("東京海上",            129492,   97056),
    ("第一ライフ",          116128,   83104),
    ("ＣＤＳ",             583416,   49950),
    ("バルカー",            128960,   95552),
    ("伊藤忠",              193987,  122902),
    ("三菱ＨＣ",             28864,   13904),
    ("アサンテ",             53770,  -16036),
    ("アビスト",             39960,    3516),
    ("沖縄セルラー",         29200,   18816),
    ("ＪＲ九州",             27480,    5992),
]
jp_nisa_growth = [
    ("キヤノン",            431000,  -56300),
    ("三菱商事(NISA)",      454000,  193900),
    ("Ｅギャランティ(N)",  335800,   78600),
    ("ＮＴＴ(NISA)",       505400,  -89600),
]
jp_old_nisa    = [("信越化学", 731000, 302700)]

jp_stock_total  = 12934193.5 + 1726200 + 731000   # 15,391,393.5
jp_stock_profit = 5827639.5  + 126600  + 302700    # 6,256,939.5
jp_stock_cost   = jp_stock_total - jp_stock_profit

# ── SBI証券 投資信託 ──
jp_fund_total  = 4253472 + 3362294   # 7,615,766
jp_fund_profit = 1140708 + 1062254   # 2,202,962
jp_fund_cost   = jp_fund_total - jp_fund_profit

# ── SBI証券 米国株 ──
us_tokutei_total  = 15952003; us_tokutei_profit = 9228213
us_nisa_total     = 2061994;  us_nisa_profit    = 562872
us_old_nisa_total = 2656243;  us_old_nisa_profit = 2293993
us_stock_total    = us_tokutei_total + us_nisa_total + us_old_nisa_total   # 20,670,240
us_stock_profit   = us_tokutei_profit + us_nisa_profit + us_old_nisa_profit  # 12,085,078

# ── SBI証券 米国債券 ──
us_bond_total  = 7170124

# ── SBI証券 預り金 ──
sbi_usd_cash   = 1_880_000   # 米ドル188万円相当
sbi_jpy_cash   = 1_200_000   # 円120万円
SBI_CASH_TOTAL = sbi_usd_cash + sbi_jpy_cash   # 3,080,000

SBI_TOTAL      = jp_stock_total + jp_fund_total + us_stock_total + us_bond_total + SBI_CASH_TOTAL

# ── 楽天証券 ──
rakuten_vti_val    = 7190827; rakuten_vti_profit  = 4340827; rakuten_vti_cost = 2850000
rakuten_spcx_val   =   89527; rakuten_spcx_profit =   24616; rakuten_spcx_cost =  64911
RAKUTEN_TOTAL      = rakuten_vti_val + rakuten_spcx_val   # 7,280,354
RAKUTEN_PROFIT     = rakuten_vti_profit + rakuten_spcx_profit  # 4,365,443
RAKUTEN_COST       = RAKUTEN_TOTAL - RAKUTEN_PROFIT

# ── 現金（SBI以外） ──
CASH = 9_000_000

# ── ポートフォリオ合計 ──
GRAND_TOTAL   = SBI_TOTAL + RAKUTEN_TOTAL + CASH    # 67,127,878
SBI_PROFIT    = jp_stock_profit + jp_fund_profit + us_stock_profit  # 20,544,980 (債券除く)
GRAND_PROFIT  = SBI_PROFIT + RAKUTEN_PROFIT          # 24,910,423
GRAND_COST    = GRAND_TOTAL - GRAND_PROFIT - us_bond_total  # 投資元本
GRAND_PROFIT_RATE = GRAND_PROFIT / (GRAND_TOTAL - GRAND_PROFIT - us_bond_total - CASH - SBI_CASH_TOTAL) * 100

# ─── ユーティリティ ───────────────────────────────────────────────────────────

def new_fig(title="", subtitle="", tc=NAVY, accent=GOLD):
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=BG)
    if title:
        ah = fig.add_axes([0, 0.88, 1, 0.12])
        ah.set_facecolor(tc); ah.axis('off')
        ah.set_xlim(0,1); ah.set_ylim(0,1)
        ah.text(0.025, 0.65, title, color=WHITE, fontsize=20, fontweight='bold', va='center')
        if subtitle:
            ah.text(0.025, 0.17, subtitle, color='#AACCEE', fontsize=9, va='center')
        ah.axhline(0, color=accent, linewidth=3)
    return fig

def bbox(ax, x, y, w, h, edge, face, **kw):
    r = FancyBboxPatch((x,y), w, h, boxstyle="round,pad=0.012",
                       linewidth=kw.get('lw',1.5), edgecolor=edge, facecolor=face,
                       transform=ax.transAxes)
    ax.add_patch(r); return r

def save_pil(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).convert('RGB')
    plt.close(fig); return img

def table_header(ax, headers, col_xs, col_ws, y, hh, bg, fg=WHITE):
    for hdr, cx, cw in zip(headers, col_xs, col_ws):
        bbox(ax, cx, y, cw-0.005, hh, bg, bg, lw=0)
        ax.text(cx+cw/2, y+hh/2, hdr, ha='center', va='center',
                fontsize=9, fontweight='bold', color=fg, transform=ax.transAxes)

def table_row(ax, vals, col_xs, col_ws, y, rh, bg, colors=None):
    for j,(val, cx, cw) in enumerate(zip(vals, col_xs, col_ws)):
        bbox(ax, cx, y, cw-0.005, rh, '#CCDDEE', bg, lw=0.5)
        clr = colors[j] if colors else NAVY
        ax.text(cx+cw/2, y+rh/2, str(val), ha='center', va='center',
                fontsize=8.5, color=clr, transform=ax.transAxes)

# ════════════════════════════════════════════════════════════════════════════
# スライド 1: 表紙
# ════════════════════════════════════════════════════════════════════════════

def slide_cover():
    fig = plt.figure(figsize=(11.69,8.27), facecolor=NAVY)
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_facecolor(NAVY)

    for x,y,r,a in [(0.88,0.88,0.22,0.06),(0.08,0.1,0.18,0.05),(0.92,0.12,0.14,0.05)]:
        ax.add_patch(plt.Circle((x,y),r,color=BLUE,alpha=a,transform=ax.transAxes))
    ax.axhline(0.44, color=GOLD, linewidth=4, xmin=0.05, xmax=0.95)

    ax.text(0.5, 0.83, "投資プラン提案レポート  ver.2", ha='center', color=WHITE,
            fontsize=28, fontweight='bold')
    ax.text(0.5, 0.70, "SBI証券 + 楽天証券 + 現金  統合分析", ha='center', color=GOLD,
            fontsize=20, fontweight='bold')
    ax.text(0.5, 0.59, "2026年6月21日  最新データ反映版", ha='center', color='#AACCEE', fontsize=12)

    kpis = [
        ("総資産（3口座合算）",  f"約 {GRAND_TOTAL/1e8:.2f} 億円",  GOLD),
        ("SBI証券",              f"{SBI_TOTAL/1e4:.0f} 万円",       '#5DADE2'),
        ("楽天証券",             f"{RAKUTEN_TOTAL/1e4:.0f} 万円",   RAKUTEN),
        ("現金（待機資金）",     f"{CASH/1e4:.0f} 万円",            GREEN),
    ]
    for i,(lbl,val,clr) in enumerate(kpis):
        x = 0.06 + i*0.23
        bbox(ax, x, 0.20, 0.21, 0.18, clr, '#1A3050', lw=2)
        ax.text(x+0.105, 0.355, lbl, ha='center', color='#AACCEE', fontsize=8,
                transform=ax.transAxes)
        ax.text(x+0.105, 0.265, val, ha='center', color=clr, fontsize=11,
                fontweight='bold', transform=ax.transAxes)

    ax.text(0.5, 0.10, "プランA: 守り重視  /  プランB: 積立継続  /  プランC: 攻め型  /  プランD: 円高対応  /  現金活用プラン",
            ha='center', color='#6688AA', fontsize=9.5)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 2: 全資産サマリー（3口座合算）
# ════════════════════════════════════════════════════════════════════════════

def slide_total_summary():
    fig = new_fig("全資産サマリー（3口座合算）",
                  f"SBI証券（預り金含む） + 楽天証券 + 現金900万円  ｜  総評価額: {GRAND_TOTAL/1e8:.2f}億円  ｜  総含み益: +{GRAND_PROFIT/1e4:.0f}万円")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # 上部KPIカード4枚
    kpis = [
        ("SBI証券 合計",   f"{SBI_TOTAL/1e4:.0f}万円",          f"含み益 +{SBI_PROFIT/1e4:.0f}万",   BLUE),
        ("楽天証券 合計",  f"{RAKUTEN_TOTAL/1e4:.0f}万円",       f"含み益 +{RAKUTEN_PROFIT/1e4:.0f}万", RAKUTEN),
        ("現金（待機）",   f"{CASH/1e4:.0f}万円",                "運用待機中",                        GREEN),
        ("総資産合計",     f"{GRAND_TOTAL/1e8:.2f}億円",         f"総含み益 +{GRAND_PROFIT/1e4:.0f}万", GOLD),
    ]
    for i,(lbl,val,sub,clr) in enumerate(kpis):
        x = 0.02 + i*0.245
        bbox(ax, x, 0.73, 0.23, 0.13, clr, WHITE, lw=2)
        ax.text(x+0.115, 0.838, lbl, ha='center', fontsize=8.5, color=GRAY,
                transform=ax.transAxes)
        ax.text(x+0.115, 0.785, val, ha='center', fontsize=13, fontweight='bold',
                color=clr, transform=ax.transAxes)
        ax.text(x+0.115, 0.742, sub, ha='center', fontsize=8, color=GRAY,
                transform=ax.transAxes)

    # 左: アセット配分 ドーナツチャート
    ax1 = fig.add_axes([0.02, 0.08, 0.40, 0.62])
    labels = ['SBI\n日本株',  'SBI\n投資信託', 'SBI\n米国株',
              'SBI\n米国債',  'SBI\n預り金', '楽天\n投資信託', '楽天\n米国株', '現金']
    sizes  = [jp_stock_total, jp_fund_total, us_stock_total,
              us_bond_total,  SBI_CASH_TOTAL, rakuten_vti_val, rakuten_spcx_val, CASH]
    colors = ['#2E86C1','#1E8B4C','#E67E22','#8E44AD',
              '#17A589','#BF0000','#FF6666','#95A5A6']
    wedges, texts, autotexts = ax1.pie(
        sizes, labels=labels, colors=colors,
        autopct=lambda p: f'{p:.1f}%' if p>2 else '',
        startangle=120, textprops={'fontsize':8.5},
        wedgeprops={'linewidth':2,'edgecolor':'white'},
        explode=[0.02]*len(sizes)
    )
    for at in autotexts:
        at.set_fontsize(8); at.set_fontweight('bold')
    ax1.set_title('全資産 アセット配分', fontsize=13, fontweight='bold', pad=6)

    # 中央: 口座別積み上げ棒グラフ
    ax2 = fig.add_axes([0.44, 0.12, 0.54, 0.58])
    cats   = ['SBI\n日本株', 'SBI\n投信', 'SBI\n米国株', 'SBI\n米国債', 'SBI\n預り金', '楽天\n投信', '楽天\n米国株', '現金']
    costs  = [jp_stock_cost, jp_fund_cost, us_stock_total-us_stock_profit,
              us_bond_total, SBI_CASH_TOTAL, rakuten_vti_cost, rakuten_spcx_cost, CASH]
    profs  = [jp_stock_profit, jp_fund_profit, us_stock_profit,
              0, 0, rakuten_vti_profit, rakuten_spcx_profit, 0]
    bcolors= ['#2E86C1','#1E8B4C','#E67E22','#8E44AD','#17A589','#BF0000','#FF6666','#95A5A6']
    x = np.arange(len(cats))
    b1 = ax2.bar(x, [c/1e6 for c in costs], 0.65, color=bcolors, edgecolor='white',
                 alpha=0.65, label='取得金額')
    b2 = ax2.bar(x, [p/1e6 for p in profs], 0.65, bottom=[c/1e6 for c in costs],
                 color=bcolors, edgecolor='white', label='評価益')
    ax2.set_xticks(x); ax2.set_xticklabels(cats, fontsize=8)
    ax2.set_ylabel('評価額（百万円）', fontsize=9)
    ax2.set_title('口座・資産クラス別  取得金額 vs 評価益', fontsize=11, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3); ax2.spines[['top','right']].set_visible(False)
    # 損益率ラベル
    for i,(p,c) in enumerate(zip(profs, costs)):
        if p > 0:
            rate = p/c*100
            ax2.text(i, (c+p)/1e6+0.15, f'+{rate:.0f}%', ha='center',
                     fontsize=8, fontweight='bold', color=bcolors[i])
    ax2.legend(['取得金額','評価益'], fontsize=9, loc='upper left')

    # 最下部バー
    bbox(ax, 0.02, 0.01, 0.96, 0.06, NAVY, NAVY, lw=0)
    ax.text(0.5, 0.055, f"総資産 {GRAND_TOTAL/1e8:.2f}億円  ｜  総含み益 +{GRAND_PROFIT/1e4:.0f}万円  ｜  損益率 +{GRAND_PROFIT/(GRAND_TOTAL-GRAND_PROFIT-us_bond_total-CASH-SBI_CASH_TOTAL)*100:.1f}%（投資部分）  ｜  現金・預り金比率 {(CASH+SBI_CASH_TOTAL)/GRAND_TOTAL*100:.1f}%",
            ha='center', fontsize=9.5, fontweight='bold', color=GOLD, transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 3: 楽天証券ポートフォリオ詳細
# ════════════════════════════════════════════════════════════════════════════

def slide_rakuten():
    fig = new_fig("楽天証券 ポートフォリオ詳細", tc=RAKUTEN, accent=GOLD,
                  subtitle=f"総評価額: {RAKUTEN_TOTAL/1e4:.0f}万円  ｜  総含み益: +{RAKUTEN_PROFIT/1e4:.0f}万円  ｜  参考為替: 161.31円/USD（06/20）")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # KPIカード
    kpis2 = [
        ("楽天・全米株式\nインデックスF(VTI)", f"{rakuten_vti_val/1e4:.0f}万円",
         f"+{rakuten_vti_profit/1e4:.0f}万 (+152.3%)", RAKUTEN),
        ("スペースX\n(SPCX)", f"{rakuten_spcx_val/1e4:.1f}万円",
         f"+{rakuten_spcx_profit/1e4:.1f}万 (+37.9%)", ORANGE),
        ("楽天証券 合計", f"{RAKUTEN_TOTAL/1e4:.0f}万円",
         f"含み益率 +{RAKUTEN_PROFIT/RAKUTEN_COST*100:.1f}%", GOLD),
    ]
    for i,(lbl,val,sub,clr) in enumerate(kpis2):
        x = 0.02 + i*0.32
        bbox(ax, x, 0.73, 0.30, 0.14, clr, WHITE, lw=2)
        ax.text(x+0.15, 0.848, lbl, ha='center', fontsize=9, color=GRAY, transform=ax.transAxes)
        ax.text(x+0.15, 0.790, val, ha='center', fontsize=14, fontweight='bold',
                color=clr, transform=ax.transAxes)
        ax.text(x+0.15, 0.745, sub, ha='center', fontsize=9, fontweight='bold',
                color=clr, transform=ax.transAxes)

    # 左: 楽天VTI vs SBI eMAXIS 比較
    ax1 = fig.add_axes([0.03, 0.10, 0.44, 0.60])
    funds = ['SBI\neMAXIS Slim\n(成長枠)', 'SBI\neMAXIS Slim\n(つみたて)', '楽天\nVTI']
    fund_vals  = [4253472, 3362294, 7190827]
    fund_costs = [3112764, 2300040, 2850000]
    fund_profs = [1140708, 1062254, 4340827]
    fund_rates = [p/c*100 for p,c in zip(fund_profs, fund_costs)]
    fund_colors= [BLUE, '#5DADE2', RAKUTEN]
    x = np.arange(len(funds))
    b1 = ax1.bar(x, [c/1e4 for c in fund_costs], 0.55, color=fund_colors,
                 edgecolor='white', alpha=0.6, label='取得金額')
    b2 = ax1.bar(x, [p/1e4 for p in fund_profs], 0.55,
                 bottom=[c/1e4 for c in fund_costs],
                 color=fund_colors, edgecolor='white', label='評価益')
    ax1.set_xticks(x); ax1.set_xticklabels(funds, fontsize=9)
    ax1.set_ylabel('金額（万円）', fontsize=9)
    ax1.set_title('インデックスファンド 3本 比較', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.35); ax1.spines[['top','right']].set_visible(False)
    ax1.legend(fontsize=9)
    for i,(p,c) in enumerate(zip(fund_profs, fund_costs)):
        rate = p/c*100
        ax1.text(i, (c+p)/1e4+5, f'+{rate:.1f}%', ha='center',
                 fontsize=10, fontweight='bold', color=fund_colors[i])

    # 右: 保有銘柄詳細テーブル
    ax.text(0.52, 0.70, "保有銘柄 詳細", fontsize=13, fontweight='bold',
            color=RAKUTEN, transform=ax.transAxes)
    headers = ["銘柄", "口座", "数量", "取得単価", "現在値", "評価額", "損益", "損益率"]
    rows = [
        ("楽天・全米株式\nインデックスF", "特定", "1,600,273口",
         "17,809円/万口", "44,935円", "719.1万円", "+434.1万円", "+152.3%"),
        ("スペースX\n(SPCX)", "特定", "3株",
         "135.00USD", "185.00USD", "8.9万円", "+2.5万円", "+37.9%"),
    ]
    cxs = [0.52, 0.67, 0.755, 0.82, 0.875, 0.925, 0.955, 0.978]
    cws = [0.145, 0.08, 0.06, 0.055, 0.048, 0.028, 0.022, 0.018]

    # ヘッダー
    for h,cx,cw in zip(headers, cxs, cws):
        bbox(ax, cx, 0.60, cw-0.003, 0.047, RAKUTEN, RAKUTEN, lw=0)
        ax.text(cx+cw/2, 0.624, h, ha='center', va='center', fontsize=7.5,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
    for i, row in enumerate(rows):
        bg = '#FFF0F0' if i%2==0 else WHITE
        ry = 0.48 - i*0.13
        for j,(val,cx,cw) in enumerate(zip(row, cxs, cws)):
            bbox(ax, cx, ry, cw-0.003, 0.11, '#FFCCCC', bg, lw=0.5)
            clr = GREEN if '+' in str(val) else (RED if '-' in str(val) else NAVY)
            fw  = 'bold' if j>=6 else 'normal'
            ax.text(cx+cw/2, ry+0.055, val, ha='center', va='center',
                    fontsize=7.5, color=clr, fontweight=fw, transform=ax.transAxes)

    # 注目ポイント
    points = [
        ("楽天VTI  +152%",  "SBI内のVTI（特定160株、+134%）と合わせ\n全米株式インデックスへの集中度が高い"),
        ("スペースX  +38%", "宇宙産業・通信衛星のリーダー。非上場から\n上場直後。米国個別成長株として継続保有"),
        ("注意",             "楽天VTI + SBI VTI = 実質「全米ETF」\nに約2,000万円弱の集中。リバランス検討"),
    ]
    for i,(title,desc) in enumerate(points):
        y = 0.33 - i*0.11
        clr = RAKUTEN if i<2 else RED
        bbox(ax, 0.52, y, 0.46, 0.095, clr, '#FFF8F8', lw=1.5)
        ax.text(0.535, y+0.065, f"● {title}", fontsize=10, fontweight='bold',
                color=clr, transform=ax.transAxes)
        ax.text(0.535, y+0.015, desc, fontsize=8.5, color=GRAY, transform=ax.transAxes)

    bbox(ax, 0.02, 0.01, 0.96, 0.06, RAKUTEN, RAKUTEN, lw=0)
    ax.text(0.5, 0.042, "楽天VTIの+152%はSBI eMAXIS Slimをはるかに凌ぐ好成績。ただしVTI系への集中（合計約1,900万円）を意識してリバランス要検討。",
            ha='center', fontsize=9.5, color=WHITE, fontweight='bold', transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 4: ポートフォリオ強み・課題（更新版）
# ════════════════════════════════════════════════════════════════════════════

def slide_swot():
    fig = new_fig("全ポートフォリオ 強み・課題分析（統合版）",
                  f"総資産 {GRAND_TOTAL/1e8:.2f}億円  ｜  総含み益 +{GRAND_PROFIT/1e4:.0f}万円  ｜  現金・預り金比率 {(CASH+SBI_CASH_TOTAL)/GRAND_TOTAL*100:.1f}%")
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    ax.text(0.25, 0.86, "強み", ha='center', fontsize=15, fontweight='bold',
            color=GREEN, transform=ax.transAxes)
    ax.text(0.75, 0.86, "課題・リスク", ha='center', fontsize=15, fontweight='bold',
            color=RED, transform=ax.transAxes)
    ax.axvline(0.5, ymin=0.09, ymax=0.84, color='#CCCCCC', linewidth=1.5, linestyle='--')

    strengths = [
        ("超高い含み益バッファー",
         "総含み益+2,491万円（+59%）。\n急落局面でも心理的余裕がある"),
        ("現金・預り金1,208万円の余力",
         "SBI預り金308万＋SBI外現金900万円\n投資機会・急落局面に即対応できる"),
        ("インデックス×個別株の2軸",
         "楽天VTI・SBI eMAXIS Slim・VTIで\n全市場に連動しつつ個別株で超過収益"),
        ("NISA非課税の活用",
         "成長・つみたて・旧NISAをフル活用\n将来の非課税収益が積み上がっている"),
        ("3口座による分散管理",
         "SBI（日米株）・楽天（インデックス）\nで運用スタイルを分離できている"),
    ]
    for i,(title,desc) in enumerate(strengths):
        y = 0.73 - i*0.133
        bbox(ax, 0.02, y-0.015, 0.44, 0.115, GREEN, '#F0FFF4', lw=1.5)
        ax.text(0.04, y+0.065, f"✓  {title}", fontsize=10.5, fontweight='bold',
                color=GREEN, transform=ax.transAxes)
        ax.text(0.057, y+0.010, desc, fontsize=8.5, color=GRAY, transform=ax.transAxes)

    challenges = [
        ("VTI系への集中リスク",
         "楽天VTI+SBI VTI+SBI特定VTI=\n約1,900万円。全体の28%超が集中"),
        ("米国資産の為替リスク",
         "米国株+債券+楽天SPCX=約2,874万円\n円高150円で約254万円相当の為替損失"),
        ("日銀利上げの継続",
         "1.0%到達後も追加利上げ見込み\nNTT・KDDI等の高配当株に逆風"),
        ("現金・預り金の機会損失",
         "SBI外900万＋SBI預り金308万が低利運用\n個人向け国債等で少なくとも0.5%以上狙える"),
        ("中東地政学リスク",
         "ホルムズ海峡リスク継続。\n原油輸入95%を中東依存の日本株に影響"),
    ]
    for i,(title,desc) in enumerate(challenges):
        y = 0.73 - i*0.133
        bbox(ax, 0.52, y-0.015, 0.44, 0.115, RED, '#FFF5F5', lw=1.5)
        ax.text(0.54, y+0.065, f"!  {title}", fontsize=10.5, fontweight='bold',
                color=RED, transform=ax.transAxes)
        ax.text(0.557, y+0.010, desc, fontsize=8.5, color=GRAY, transform=ax.transAxes)

    bbox(ax, 0.02, 0.01, 0.96, 0.065, NAVY, NAVY, lw=0)
    ax.text(0.5, 0.045, "最重要アクション：①VTI系集中のリバランス  ②現金・預り金計1,208万円の有効活用  ③円高シナリオへの段階的対応",
            ha='center', fontsize=10, fontweight='bold', color=GOLD, transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 5: 現金900万円 活用プラン
# ════════════════════════════════════════════════════════════════════════════

def slide_cash():
    fig = new_fig("現金900万円 活用プラン", tc=GREEN, accent=GOLD,
                  subtitle="SBI証券以外の待機資金900万円の最適な運用方法を提案します")
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    bbox(ax, 0.02,0.83, 0.96,0.04, GREEN, '#E9F7EF', lw=0)
    ax.text(0.5, 0.853, "基本方針：現金の一部は流動性を確保しつつ、安全資産→インカム→成長の順に段階的に運用へ移行",
            ha='center', fontsize=10, fontweight='bold', color='#145A32', transform=ax.transAxes)

    allocs = [
        (0.30, 2700000, "個人向け国債\n（変動10年型）",
         "#145A32", "#D5F5E3",
         ["日銀利上げで利率が連動上昇（現在0.5%超）",
          "元本保証・1万円から購入可能",
          "1年後から換金可能（中途解約可）",
          "まず安全性最優先の270万円を移行"]),
        (0.30, 2700000, "NISA成長投資枠\n一括・積立追加",
         BLUE, "#D6EAF8",
         ["年間240万円枠を最大活用",
          "eMAXIS Slim オールカントリーを追加",
          "一括購入 or 12ヶ月分割（150万+毎月12.5万）",
          "長期での税メリット最大化"]),
        (0.20, 1800000, "国内高配当株\n打診買い",
         ORANGE, "#FEF9E7",
         ["日銀利上げ恩恵株（三菱UFJ・東京海上）を追加",
          "配当利回り3〜4%以上が目標",
          "NISA成長枠で購入し非課税配当を享受",
          "円高でも内需株は為替影響が小さい"]),
        (0.20, 1800000, "緊急予備金\n（MRF/普通預金）",
         GRAY, "#F2F3F4",
         ["生活費6ヶ月分+投資機会用待機資金",
          "市場急落時の「買い場」対応資金",
          "日銀利上げで普通預金金利も上昇中",
          "流動性を最優先。すぐ動かせる状態を保持"]),
    ]

    for i,(pct, amt, title, clr, bg, points) in enumerate(allocs):
        col = i % 2
        row = i // 2
        x = 0.02 + col*0.49
        y = 0.44 - row*0.40

        bbox(ax, x, y, 0.47, 0.37, clr, bg, lw=2)

        # タイトルバー
        bbox(ax, x, y+0.285, 0.47, 0.075, clr, clr, lw=0)
        ax.text(x+0.12, y+0.323, f"{pct*100:.0f}%  |  {amt/1e4:.0f}万円", fontsize=11,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
        ax.text(x+0.32, y+0.323, title, fontsize=9.5, fontweight='bold',
                color=WHITE, transform=ax.transAxes)

        for j, pt in enumerate(points):
            ax.text(x+0.025, y+0.240-j*0.060, f"• {pt}", fontsize=8.5,
                    color=GRAY, transform=ax.transAxes)

    # 配分パイチャート
    ax2 = fig.add_axes([0.36, 0.04, 0.28, 0.38])
    sizes2 = [2700000, 2700000, 1800000, 1800000]
    labs2  = ['個人向け\n国債\n30%', 'NISA\n積立\n30%', '高配当株\n20%', '予備金\n20%']
    cols2  = ['#145A32', BLUE, ORANGE, GRAY]
    ax2.pie(sizes2, labels=labs2, colors=cols2, autopct='%1.0f%%',
            startangle=90, textprops={'fontsize':8.5},
            wedgeprops={'linewidth':2,'edgecolor':'white'},
            explode=[0.03]*4)
    ax2.set_title('900万円 推奨配分', fontsize=11, fontweight='bold')

    bbox(ax, 0.02,0.01, 0.96,0.05, GREEN, GREEN, lw=0)
    ax.text(0.5, 0.038, "優先順位：まず国債270万（安全）→ NISA積立270万（長期）→ 高配当株180万（インカム）→ 予備180万（流動性）",
            ha='center', fontsize=9.5, color=WHITE, fontweight='bold', transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 6: プランA（守り重視型）
# ════════════════════════════════════════════════════════════════════════════

def slide_plan_a():
    fig = new_fig("プランA：守り重視・利益確定型", tc='#145A32', accent=GREEN,
                  subtitle="推奨対象：リスクを抑えたい方 / 円高・株安シナリオ優先 / リスク許容度：低〜中")
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    bbox(ax, 0.02,0.83, 0.96,0.04, '#145A32', '#D5F5E3', lw=0)
    ax.text(0.5, 0.852, "戦略の核心：大幅含み益銘柄を一部利益確定。現金900万円を安全資産・NISA積立に振り向けVTI集中を解消",
            ha='center', fontsize=10, fontweight='bold', color='#145A32', transform=ax.transAxes)

    actions = [
        ("SELL",  GREEN,    "三井物産（8031）",        "200株",   "+143万確定。+239%達成済み、高値圏での部分確定"),
        ("SELL",  GREEN,    "楽天VTI → 一部解約",     "200万円分","SBI VTIと合算で集中リスク解消。+152%の利益確定"),
        ("SELL",  GREEN,    "VTI（SBI特定）",          "80株",    "円高前にドルを円転。残100株は継続保有"),
        ("SELL",  GREEN,    "SKYT（旧NISA）",          "200株",   "+578%の旧NISA株。一部確定で利益を守る"),
        ("BUY",   BLUE,     "個人向け国債（変動10年）", "現金270万","日銀利上げで利回り上昇中。元本保証"),
        ("ADD",   BLUE,     "NISA積立増額",            "現金から月10万","eMAXIS Slim 積立継続・一括追加"),
        ("HOLD",  GRAY,     "その他全ポジション",      "現状維持", "含み益のある銘柄はそのまま継続保有"),
    ]
    # ヘッダー
    hds = ["操作", "銘柄・商品", "数量・金額", "理由"]
    cxs = [0.02, 0.09, 0.245, 0.365]; cws = [0.065, 0.15, 0.12, 0.60]
    table_header(ax, hds, cxs, cws, 0.76, 0.042, '#145A32')
    for i,(op,clr,name,qty,reason) in enumerate(actions):
        bg  = '#F0FFF4' if i%2==0 else WHITE
        ry  = 0.705 - i*0.079
        vals = [op, name, qty, reason]
        cs   = [clr if j==0 else (GREEN if op=='BUY' or op=='ADD' else (GRAY if op=='HOLD' else GREEN))
                if j==0 else NAVY for j in range(4)]
        for j,(val,cx,cw) in enumerate(zip(vals, cxs, cws)):
            bbox(ax, cx, ry, cw-0.005, 0.071, '#AACCAA', bg, lw=0.5)
            fw = 'bold' if j==0 else 'normal'
            c  = (GREEN if op in ['SELL','ADD','BUY'] else GRAY) if j==0 else NAVY
            ax.text(cx+cw/2, ry+0.035, val, ha='center', va='center',
                    fontsize=8.5, color=c, fontweight=fw, transform=ax.transAxes)

    # 右: リバランス後の配分
    ax2 = fig.add_axes([0.01, 0.06, 0.35, 0.20])
    ax2.set_facecolor('#F8FBFF'); ax2.axis('off')
    ax2.set_xlim(0,1); ax2.set_ylim(0,1)
    ax2.text(0.5, 0.92, "リバランス後 想定配分", ha='center', fontsize=10,
             fontweight='bold', color='#145A32', transform=ax2.transAxes)
    items = [("日本株","23%",BLUE),("米国株","29%",ORANGE),
             ("投資信託","20%",GREEN),("国債・安全資産","17%",PURPLE),("現金","11%",GRAY)]
    for i,(lbl,pct,clr) in enumerate(items):
        x = i/5
        ax2.barh(0.3, float(pct[:-1]), left=sum(float(items[j][1][:-1]) for j in range(i)),
                 height=0.25, color=clr, edgecolor='white')
    ax2.text(0.5, 0.05, "日本株23% / 米国株29% / 投信20% / 債券・安全17% / 現金11%",
             ha='center', fontsize=8, color=GRAY, transform=ax2.transAxes)

    bbox(ax, 0.02,0.01, 0.96,0.05, '#145A32', '#145A32', lw=0)
    pts = ["利益確定でリスク低減","VTI集中解消でバランス改善","個人向け国債で利上げを享受"]
    for i,pt in enumerate(pts):
        ax.text(0.04+i*0.33, 0.040, f"✓ {pt}", fontsize=9.5, color=WHITE,
                fontweight='bold', transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 7: プランB（積立継続型）
# ════════════════════════════════════════════════════════════════════════════

def slide_plan_b():
    fig = new_fig("プランB：積立継続・現状維持型", tc=BLUE, accent=GOLD,
                  subtitle="推奨対象：長期・安定運用重視 / 現ポートフォリオを活かす / リスク許容度：中")
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    bbox(ax, 0.02,0.83, 0.96,0.04, BLUE, '#D6EAF8', lw=0)
    ax.text(0.5, 0.852, "戦略の核心：ポジションをほぼ維持。現金900万円を活用してNISA積立を強化し複利効果を最大化する",
            ha='center', fontsize=10, fontweight='bold', color=BLUE, transform=ax.transAxes)

    b_actions = [
        ("HOLD", GRAY,   "全ポジション継続保有",
         "大幅含み益。長期保有が基本。日々の価格変動に惑わされない"),
        ("ADD",  BLUE,   "eMAXIS Slim（SBI NISA成長枠）追加",
         "現金270万→一括投資 + 月10万積立継続。年240万枠フル活用"),
        ("ADD",  BLUE,   "楽天VTI 継続積立",
         "楽天口座でも毎月積立を継続（月3〜5万）。楽天ポイント投資も活用"),
        ("DRIP", GREEN,  "配当金・分配金の再投資",
         "NTT・KDDI・オリックス・三菱商事等の配当をeMAXIS Slimへ自動再投資"),
        ("HOLD", GRAY,   "米国債4本 満期まで保有",
         "金利収入（USD）を積み上げ。2027年満期後は円建て国債へ移行検討"),
        ("WAIT", ORANGE, "残り現金（約450万）は待機資金",
         "相場急落時（日経-10%以上）の買い増しチャンスに備えて保持"),
    ]
    for i,(op,clr,name,reason) in enumerate(b_actions):
        y = 0.72 - i*0.115
        bbox(ax, 0.02, y, 0.46, 0.100, clr, '#F0F8FF', lw=1.5)
        op_rect = FancyBboxPatch((0.03, y+0.030), 0.055, 0.040,
                                  boxstyle="round,pad=0.005", lw=0,
                                  facecolor=clr, transform=ax.transAxes)
        ax.add_patch(op_rect)
        ax.text(0.057, y+0.052, op, ha='center', va='center', fontsize=8,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
        ax.text(0.098, y+0.070, name, fontsize=9.5, fontweight='bold',
                color=NAVY, transform=ax.transAxes)
        ax.text(0.098, y+0.022, reason, fontsize=8.5, color=GRAY, transform=ax.transAxes)

    # 右: 資産推移シミュレーション（現金投入後）
    ax2 = fig.add_axes([0.52, 0.28, 0.45, 0.52])
    years = np.arange(0, 11)
    base  = GRAND_TOTAL
    monthly = 13 * 10000  # 月13万積立
    rate6 = 0.06; rate4 = 0.04
    grow6 = [base*(1+rate6)**y + monthly*12*((1+rate6)**y-1)/rate6 for y in years]
    grow4 = [base*(1+rate4)**y + monthly*12*((1+rate4)**y-1)/rate4 for y in years]
    flat  = [base + monthly*12*y for y in years]
    ax2.fill_between(years, [v/1e8 for v in grow4], [v/1e8 for v in grow6],
                     alpha=0.20, color=BLUE, label='年率4〜6%想定レンジ')
    ax2.plot(years, [v/1e8 for v in flat],  'o--', color=GRAY, lw=1.5, ms=5, label='積立のみ(0%)')
    ax2.plot(years, [v/1e8 for v in grow4], 'o-',  color='#5DADE2', lw=2, ms=6, label='年率4%')
    ax2.plot(years, [v/1e8 for v in grow6], 'o-',  color=BLUE, lw=2.5, ms=7, label='年率6%')
    ax2.set_xlabel('経過年数', fontsize=10)
    ax2.set_ylabel('総資産（億円）', fontsize=10)
    ax2.set_title(f'月13万積立 資産推移シミュレーション\n（現在{GRAND_TOTAL/1e8:.2f}億円スタート）',
                  fontsize=11, fontweight='bold')
    ax2.legend(fontsize=9); ax2.grid(alpha=0.3)
    ax2.spines[['top','right']].set_visible(False)
    for arr, lbl in [(grow6, f'{grow6[-1]/1e8:.1f}億\n(+6%)'),
                     (grow4, f'{grow4[-1]/1e8:.1f}億\n(+4%)')]:
        ax2.annotate(lbl, xy=(10, arr[-1]/1e8), xytext=(10.1, arr[-1]/1e8),
                     fontsize=9, fontweight='bold', va='center',
                     color=BLUE if arr is grow6 else '#5DADE2')

    bbox(ax, 0.02,0.01, 0.96,0.05, BLUE, BLUE, lw=0)
    pts = ["NISA枠フル活用で非課税益を積み上げ","月13万積立継続で複利効果最大化","急落時の買い増し原資450万を確保"]
    for i,pt in enumerate(pts):
        ax.text(0.04+i*0.33, 0.040, f"✓ {pt}", fontsize=9.5, color=WHITE,
                fontweight='bold', transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 8: プランC（攻め型）
# ════════════════════════════════════════════════════════════════════════════

def slide_plan_c():
    fig = new_fig("プランC：攻め型・成長株追加型", tc='#6C3483', accent=GOLD,
                  subtitle="推奨対象：高リターン優先 / 現含み益バッファーを活用 / リスク許容度：高")
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    bbox(ax, 0.02,0.83, 0.96,0.04, PURPLE, '#E8DAEF', lw=0)
    ax.text(0.5, 0.852, "戦略の核心：現金900万円の一部をAI・半導体・宇宙産業等の成長テーマへ集中投資。既存の含み益+2,491万がリスク緩衝材",
            ha='center', fontsize=10, fontweight='bold', color=PURPLE, transform=ax.transAxes)

    # 左: 追加候補テーブル
    ax.text(0.02, 0.80, "現金からの追加投資候補（優先順）", fontsize=12,
            fontweight='bold', color=PURPLE, transform=ax.transAxes)
    cands = [
        ("AI半導体", PURPLE, [
            ("NVDA エヌビディア",        "現金200万",   "AI半導体の絶対王者。データセンター需要拡大中"),
            ("AMAT アプライドマテリアル","現金100万",   "半導体製造装置。AIチップ増産の設備投資恩恵"),
        ]),
        ("宇宙・衛星", ORANGE, [
            ("SPCX スペースX 追加",      "現金50万",    "楽天口座で既保有。スターリンク通信の急成長"),
            ("RKLB ロケットラボ",        "現金50万",    "小型ロケット打ち上げ。スペースXに次ぐ成長企業"),
        ]),
        ("国内AI関連", BLUE, [
            ("6857 アドバンテスト",       "現金100万",   "半導体テスト機器。AIチップ増産の直接恩恵"),
            ("6920 レーザーテック",       "現金100万",   "EUV検査装置。国内随一の半導体関連"),
        ]),
    ]
    y_base = 0.72
    for sect, clr, stocks in cands:
        bbox(ax, 0.02, y_base, 0.46, 0.038, clr, clr, lw=0)
        ax.text(0.25, y_base+0.021, sect, ha='center', fontsize=10,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
        for j,(ticker,amt,desc) in enumerate(stocks):
            y = y_base - 0.040 - j*0.080
            bbox(ax, 0.02, y, 0.46, 0.072, clr, '#FAF0FF', lw=1)
            ax.text(0.04, y+0.048, ticker, fontsize=9.5, fontweight='bold',
                    color=clr, transform=ax.transAxes)
            ax.text(0.30, y+0.048, amt, fontsize=9.5, fontweight='bold',
                    color=GREEN, transform=ax.transAxes)
            ax.text(0.04, y+0.012, desc, fontsize=8, color=GRAY, transform=ax.transAxes)
        y_base -= 0.040 + len(stocks)*0.080 + 0.015

    # 右: 現金600万の配分と期待値
    ax.text(0.52, 0.80, "現金600万 成長テーマ配分イメージ", fontsize=12,
            fontweight='bold', color=PURPLE, transform=ax.transAxes)
    ax2 = fig.add_axes([0.52, 0.40, 0.44, 0.38])
    categories = ['NVDA\n200万', 'AMAT\n100万', 'SPCX追加\n50万',
                  'RKLB\n50万', 'ADV\n100万', 'LT\n100万']
    vals_c = [200,100,50,50,100,100]
    cols_c = [PURPLE,'#9B59B6',ORANGE,'#F0A500',BLUE,'#5DADE2']
    wedges,texts,autotexts = ax2.pie(vals_c, labels=categories, colors=cols_c,
        autopct='%1.0f%%', startangle=90, textprops={'fontsize':8.5},
        wedgeprops={'linewidth':2,'edgecolor':'white'}, explode=[0.03]*6)
    for at in autotexts: at.set_fontsize(8); at.set_fontweight('bold')
    ax2.set_title('成長株への投資配分（計600万）', fontsize=11, fontweight='bold')

    # 注意カード
    bbox(ax, 0.52, 0.22, 0.46, 0.165, RED, '#FFF0F0', lw=2)
    ax.text(0.745, 0.363, "! リスク管理の原則", ha='center', fontsize=11,
            fontweight='bold', color=RED, transform=ax.transAxes)
    risks = ["1銘柄への投資は総資産の3〜5%以内（200〜300万円）",
             "損切りライン：取得価格から-20〜30%で撤退",
             "残り300万は予備・急落時の買い増し原資として保持",
             "NISA成長枠で購入し非課税メリット最大化"]
    for i,r in enumerate(risks):
        ax.text(0.535, 0.330-i*0.028, f"• {r}", fontsize=8.5, color=RED,
                transform=ax.transAxes)

    bbox(ax, 0.02,0.01, 0.96,0.05, PURPLE, PURPLE, lw=0)
    pts = ["含み益+2,491万がリスク緩衝材","AI・宇宙・半導体で次世代テーマを取込","残300万は相場急落の買い増し原資"]
    for i,pt in enumerate(pts):
        ax.text(0.04+i*0.33, 0.040, f"✓ {pt}", fontsize=9.5, color=WHITE,
                fontweight='bold', transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 9: プランD（円高対応型）
# ════════════════════════════════════════════════════════════════════════════

def slide_plan_d():
    fig = new_fig("プランD：円高対応・国内回帰型", tc='#784212', accent=ORANGE,
                  subtitle="推奨対象：円高シナリオ（150円台）に備えたい方 / リスク許容度：低〜中")
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    bbox(ax, 0.02,0.83, 0.96,0.04, '#784212', '#FAD7A0', lw=0)
    ax.text(0.5, 0.852, "戦略の核心：米国資産2,874万円の為替リスクを段階的にヘッジ。現金900万円は全て円建て安全資産へ",
            ha='center', fontsize=10, fontweight='bold', color='#784212', transform=ax.transAxes)

    d_actions = [
        ("SELL", RED,    "VTI（SBI特定）段階売却",
         "円高が進むたびに20〜30株ずつ段階売却。159→155→150円で3段階に分けて実施。\n「円高で損をする前に円転」戦略。"),
        ("SELL", RED,    "楽天VTI 一部解約（300万円）",
         "+152%の大幅益を一部確定。300万円分を解約し円建て資産へ。残りは継続保有。\nVTI系集中の解消にも一石二鳥。"),
        ("SELL", RED,    "AMBQ（SBI特定）全売却",
         "米国小型株。取得比+178%。円高・ドル安が進む前に全売却し利益確定。\n円建て高配当株へ置き換え。"),
        ("BUY",  ORANGE, "国内金融株（三菱UFJ等）追加",
         "日銀利上げで銀行・保険は追い風。円高でも内需株は影響軽微。\n現金200万＋VTI売却代金を活用。"),
        ("BUY",  GREEN,  "個人向け国債（変動10年）全額",
         "現金900万円を全額・個人向け国債へ。日銀利上げ継続で利率が毎年上昇。\n元本保証で最も安全な円建て運用。"),
    ]
    for i,(op,clr,name,reason) in enumerate(d_actions):
        y = 0.72 - i*0.122
        bbox(ax, 0.02, y, 0.46, 0.108, clr, '#FFF8F0', lw=1.5)
        op_r = FancyBboxPatch((0.03,y+0.030),0.060,0.040,boxstyle="round,pad=0.005",
                               lw=0,facecolor=clr,transform=ax.transAxes)
        ax.add_patch(op_r)
        ax.text(0.060, y+0.052, op, ha='center', va='center', fontsize=8,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
        ax.text(0.107, y+0.078, name, fontsize=9.5, fontweight='bold',
                color=NAVY, transform=ax.transAxes)
        ax.text(0.107, y+0.020, reason, fontsize=7.8, color=GRAY, transform=ax.transAxes)

    # 右: 為替シナリオ 損益シミュレーション
    ax2 = fig.add_axes([0.52, 0.30, 0.45, 0.50])
    fx = [159, 155, 152, 150, 146, 140]
    us_total = 27840364  # 米国株+債券+楽天SPCX
    diffs = [(us_total * r/159 - us_total)/1e4 for r in fx]
    cols  = [GREEN if d>=0 else RED for d in diffs]
    bars  = ax2.bar(range(len(fx)), diffs, color=cols, edgecolor='white', width=0.65)
    ax2.set_xticks(range(len(fx)))
    ax2.set_xticklabels([f'{r}円' for r in fx], fontsize=10)
    ax2.set_ylabel('円換算 増減（万円）', fontsize=9)
    ax2.set_title('為替変動による米国資産（2,874万円）\n円換算損益シミュレーション', fontsize=10, fontweight='bold')
    ax2.axhline(0, color=GRAY, linewidth=1)
    ax2.grid(axis='y', alpha=0.35); ax2.spines[['top','right']].set_visible(False)
    for bar,d in zip(bars,diffs):
        y_t = bar.get_height() + (3 if d>=0 else -8)
        ax2.text(bar.get_x()+bar.get_width()/2, y_t, f'{d:+.0f}万',
                 ha='center', fontsize=9, fontweight='bold', color=(GREEN if d>=0 else RED))
    ax2.axvline(2.5, color=RED, linewidth=1.5, linestyle='--', alpha=0.7)
    ax2.text(2.6, min(diffs)*0.6, '野村証券\n年末予想\n152.5円', fontsize=8, color=RED)

    # 下部コメント
    bbox(ax, 0.52, 0.10, 0.46, 0.17, ORANGE, '#FFF8EE', lw=1.5)
    ax.text(0.745, 0.248, "プランD実施で期待できる効果", ha='center', fontsize=11,
            fontweight='bold', color='#784212', transform=ax.transAxes)
    effs = ["円高150円でも米国資産損失を大幅軽減",
            "個人向け国債で日銀利上げの恩恵を獲得",
            "内需・金融株で国内景気回復の恩恵"]
    for i,e in enumerate(effs):
        ax.text(0.535, 0.215-i*0.035, f"✓ {e}", fontsize=9, color='#784212',
                transform=ax.transAxes)

    bbox(ax, 0.02,0.01, 0.96,0.05, '#784212', '#784212', lw=0)
    pts = ["円高150円で約-254万円の為替損失を事前回避","内需・金融株で利上げ・円高に強いポートフォリオへ","個人向け国債で待機資金も有効活用"]
    for i,pt in enumerate(pts):
        ax.text(0.035+i*0.33, 0.038, f"! {pt}", fontsize=8.8, color=WHITE,
                fontweight='bold', transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 10: 4プラン比較マトリックス
# ════════════════════════════════════════════════════════════════════════════

def slide_comparison():
    fig = new_fig("5プラン 比較マトリックス",
                  "リスク許容度・投資目標・市場観に応じて選択（複数プランの組み合わせも推奨）")
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # レーダーチャート
    categories = ['リターン\n期待値','リスク\n抑制','円高\n耐性','NISA\n活用','現金\n活用度']
    N = len(categories)
    angles = [n/float(N)*2*np.pi for n in range(N)] + [0]

    plan_data = {
        'A:守り重視':  ([3,5,4,3,4], '#145A32'),
        'B:積立継続':  ([4,4,3,5,4], BLUE),
        'C:攻め型':    ([5,2,2,4,5], PURPLE),
        'D:円高対応':  ([3,4,5,3,5], '#784212'),
        '現金活用':    ([3,5,5,4,5], GREEN),
    }
    ax_r = fig.add_axes([0.01, 0.08, 0.36, 0.70])
    ax_r.set_facecolor(BG); ax_r.axis('off')
    ax_r.set_xlim(-1.4,1.4); ax_r.set_ylim(-1.5,1.5)
    ax_r.set_title('プラン別 評価レーダー', fontsize=11, fontweight='bold', pad=2)
    for lv in [1,2,3,4,5]:
        pts=[[lv/5*np.cos(a),lv/5*np.sin(a)] for a in angles[:-1]]
        pts.append(pts[0])
        ax_r.plot([p[0] for p in pts],[p[1] for p in pts],color=GRAY,lw=0.5,alpha=0.4)
    for a in angles[:-1]:
        ax_r.plot([0,np.cos(a)],[0,np.sin(a)],color=GRAY,lw=0.5,alpha=0.4)
    for lbl,(scores,clr) in plan_data.items():
        vs=[s/5 for s in scores]+[scores[0]/5]
        xs=[v*np.cos(a) for v,a in zip(vs,angles)]
        ys=[v*np.sin(a) for v,a in zip(vs,angles)]
        ax_r.fill(xs,ys,alpha=0.10,color=clr)
        ax_r.plot(xs,ys,color=clr,lw=2,label=lbl)
    for cat,angle in zip(categories,angles[:-1]):
        ax_r.text(1.18*np.cos(angle),1.18*np.sin(angle),cat,
                  ha='center',va='center',fontsize=8,fontweight='bold',color=NAVY)
    ax_r.legend(loc='lower center',bbox_to_anchor=(0.5,-0.18),ncol=3,fontsize=8)

    # 比較テーブル
    ax_t = fig.add_axes([0.39, 0.08, 0.60, 0.70])
    ax_t.axis('off'); ax_t.set_xlim(0,1); ax_t.set_ylim(0,1)
    hdrs = ["", "A:守り重視", "B:積立継続", "C:攻め型", "D:円高対応", "現金活用"]
    rows = [
        ("想定期間",    "〜1年",         "5〜10年",     "3〜5年",    "1〜2年",      "即時〜1年"),
        ("現金の使い道", "国債+NISA",    "NISA増額\n積立継続", "成長株\n600万投入", "全額\n国債へ",  "30/30/20/20\n4分割"),
        ("期待リターン", "★★☆☆☆",    "★★★☆☆",   "★★★★★","★★☆☆☆",  "★★★☆☆"),
        ("リスク水準",  "低",            "中",          "高",        "低〜中",       "低"),
        ("円高耐性",    "中〜高",        "中",          "低",        "高",           "高"),
        ("VTI集中解消", "○",             "△",           "△",         "◎",           "○"),
        ("向いている人","利確・守り\n優先","長期コツコツ","高リターン\n狙い","円高を\n強く懸念","バランス\n重視"),
    ]
    cws = [0.155,0.155,0.155,0.155,0.155,0.170]
    cxs = [0.01]
    for w in cws[:-1]: cxs.append(cxs[-1]+w)
    hcs = [NAVY,'#145A32',BLUE,PURPLE,'#784212',GREEN]
    for j,(h,cx,cw,hc) in enumerate(zip(hdrs,cxs,cws,hcs)):
        bbox(ax_t,cx,0.925,cw-0.005,0.065,hc,hc,lw=0)
        ax_t.text(cx+cw/2,0.958,h,ha='center',va='center',fontsize=8.5,
                  fontweight='bold',color=WHITE,transform=ax_t.transAxes)
    for i,row in enumerate(rows):
        bg='#F5F5F5' if i%2==0 else WHITE
        ry=0.790-i*0.120
        for j,(val,cx,cw) in enumerate(zip(row,cxs,cws)):
            bbox(ax_t,cx,ry,cw-0.005,0.112,'#CCCCCC',bg,lw=0.5)
            ax_t.text(cx+cw/2,ry+0.056,val,ha='center',va='center',fontsize=8.5,
                      color=(NAVY if j==0 else GRAY),fontweight=('bold' if j==0 else 'normal'),
                      transform=ax_t.transAxes)

    bbox(ax, 0.02,0.01, 0.96,0.06, NAVY, NAVY, lw=0)
    ax.text(0.5, 0.045, "推奨組み合わせ例：「プランB（基本）＋プランA（VTI一部利確）」or「プランB（基本）＋現金活用プラン」",
            ha='center', fontsize=10, fontweight='bold', color=GOLD, transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 11: アクションスケジュール
# ════════════════════════════════════════════════════════════════════════════

def slide_timeline():
    fig = new_fig("推奨アクションスケジュール（今後12ヶ月）",
                  "市場イベントと連動した投資行動タイムライン  ｜  2026年6月〜2027年6月")
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    ax.axhline(0.52, xmin=0.04, xmax=0.96, color=NAVY, linewidth=2.5)
    months = ['6月','7月','8月','9月','10月','11月','12月','1月','2月','3月','4月','5月']
    n = len(months)
    xs = [0.05 + i*(0.90/(n-1)) for i in range(n)]
    for i,(x,m) in enumerate(zip(xs,months)):
        ax.plot(x, 0.52, 'o', ms=9, color=BLUE, zorder=5)
        ax.text(x, 0.455, m, ha='center', fontsize=8, color=GRAY, rotation=30)

    # 上部イベント
    ev_up = [
        (0,  "日銀1.0%\n利上げ済",    RED,    0.74),
        (2,  "米国\n決算期",           ORANGE, 0.68),
        (5,  "米中間\n選挙",           PURPLE, 0.74),
        (6,  "日銀追加\n利上げ予想",   RED,    0.68),
        (10, "NISA枠\n残高確認",       BLUE,   0.74),
        (11, "国債MF164\n満期（来年9月）", GREEN, 0.68),
    ]
    for idx,lbl,clr,y in ev_up:
        x=xs[idx]
        ax.annotate('',xy=(x,0.54),xytext=(x,y-0.06),
                    arrowprops=dict(arrowstyle='->',color=clr,lw=1.5))
        bbox(ax, x-0.052,y-0.06, 0.104,0.068,clr,WHITE,lw=1.5)
        ax.text(x, y-0.025, lbl, ha='center', va='center', fontsize=7.5,
                color=clr, fontweight='bold', transform=ax.transAxes)

    # 下部アクション
    ac_dn = [
        (0,  GREEN,  0.40, "現金→\n国債270万"),
        (0,  BLUE,   0.30, "NISA積立\n増額開始"),
        (1,  PURPLE, 0.40, "成長株\n打診買い"),
        (2,  ORANGE, 0.30, "高配当株\n追加検討"),
        (3,  RED,    0.40, "円高進行なら\nVTI段階売却"),
        (5,  BLUE,   0.30, "楽天VTI\n一部解約検討"),
        (6,  RED,    0.40, "金融株追加\n（利上げ恩恵）"),
        (8,  ORANGE, 0.30, "三井物産\n利益確定検討"),
        (10, BLUE,   0.40, "NISA枠\n使い切り"),
        (11, GREEN,  0.30, "来年国債\n再投資先検討"),
    ]
    for idx,clr,y,lbl in ac_dn:
        x=xs[idx]
        ax.annotate('',xy=(x,0.50),xytext=(x,y+0.075),
                    arrowprops=dict(arrowstyle='->',color=clr,lw=1.5))
        bbox(ax, x-0.052,y-0.005, 0.104,0.080,clr,'#FAFAFA',lw=1.5)
        ax.text(x, y+0.035, lbl, ha='center', va='center', fontsize=7.5,
                color=clr, fontweight='bold', transform=ax.transAxes)

    # 免責事項
    bbox(ax, 0.02,0.01, 0.96,0.095, RED, '#FFF5F5', lw=1)
    ax.text(0.5, 0.075, "免責事項：本資料は2026年6月21日時点のデータに基づく情報提供を目的としたものであり、特定の投資を推奨するものではありません。",
            ha='center', fontsize=9, color=RED, fontweight='bold', transform=ax.transAxes)
    ax.text(0.5, 0.038, "投資判断は必ずご自身の責任において行ってください。市場環境は常に変動します。記載の数値・予測は将来を保証するものではありません。",
            ha='center', fontsize=8.5, color=GRAY, transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# PDF 出力
# ════════════════════════════════════════════════════════════════════════════

OUTPUT_DIR = "/Users/takahiroazuma/Desktop/kabu/claude/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "investment_plan_v2.pdf")

slides = [
    slide_cover,
    slide_total_summary,
    slide_rakuten,
    slide_swot,
    slide_cash,
    slide_plan_a,
    slide_plan_b,
    slide_plan_c,
    slide_plan_d,
    slide_comparison,
    slide_timeline,
]

A4_W = int(297 * 150 / 25.4)
A4_H = int(210 * 150 / 25.4)

print("投資プラン PDF v2 を生成中...")
print(f"  総資産: {GRAND_TOTAL/1e8:.2f}億円 (SBI:{SBI_TOTAL/1e4:.0f}万 + 楽天:{RAKUTEN_TOTAL/1e4:.0f}万 + 現金:{CASH/1e4:.0f}万)")
print(f"  総含み益: +{GRAND_PROFIT/1e4:.0f}万円")
pil_images = []
for i,fn in enumerate(slides):
    print(f"  スライド {i+1:2d}/{len(slides)}: {fn.__name__}")
    fig = fn()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).convert('RGB').resize((A4_W,A4_H), Image.LANCZOS)
    pil_images.append(img)
    plt.close(fig)

pil_images[0].save(OUTPUT_PATH, save_all=True, append_images=pil_images[1:], resolution=150)
size_kb = os.path.getsize(OUTPUT_PATH) // 1024
print(f"\n✅ 保存完了: {OUTPUT_PATH}")
print(f"   ファイルサイズ: {size_kb} KB / {len(slides)} ページ")
