#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SBI 保有証券 ポートフォリオ分析 v2 — design01.pdf スタイル
出力: output/portfolio_report_v2.pdf
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
import numpy as np, io, os, warnings
from PIL import Image
warnings.filterwarnings('ignore')

import matplotlib.font_manager as fm
_JP = next((f.name for f in fm.fontManager.ttflist
            if f.name in ['Hiragino Sans','Hiragino Kaku Gothic ProN',
                          'Yu Gothic','Noto Sans CJK JP']), None)
if _JP: plt.rcParams['font.family'] = _JP
plt.rcParams['axes.unicode_minus'] = False

# ── デザイントークン ─────────────────────────────────────────────
BG     = '#EDEAE6'
TEXT   = '#1A1A1A'
TEXT2  = '#6B6560'
TEAL   = '#00B4CC'
BLUE1  = '#5BAED0'
BLUE2  = '#8EC8E8'
AMBER  = '#D4820C'
PURPLE = '#8870CC'
POS    = '#2D8A50'
NEG    = '#C03030'
FOOTER = '#1C1C1C'
WHITE  = '#FFFFFF'
HDRBG  = '#D4D0CC'
ALTBG  = '#F5F2EE'
BORDER = '#C8C4BE'

# ── データ ──────────────────────────────────────────────────────
jp_tokutei = [
    ("ＪＡＣリク",       1852880,  881920),
    ("三井物産",         1968192, 1368144),
    ("三菱商事(特)",      678986,  333718),
    ("武田薬品",         1178980,  352220),
    ("蔵王産業",         1437207,  502480),
    ("ＮＴＴ(特)",      1228770,  213120),
    ("ＫＤＤＩ",         591586,  227794),
    ("オリックス",      1093261,  741234),
    ("三菱ＵＦＪ",       1342868,  564540),
    ("Ｅギャランティ(特)", 553500,  149100),
    ("三井住友",          265746,  213057),
    ("ジャックス",        369000,  100700),
    ("東京海上",          136962,  104526),
    ("第一ライフ",        119104,   86080),
    ("ＣＤＳ",           567765,   34299),
    ("バルカー",          108480,   75072),
    ("伊藤忠",            197820,  126735),
    ("三菱ＨＣ",           30019,   15059),
    ("アサンテ",           56658,  -13148),
    ("アビスト",           41400,    4956),
    ("沖縄セルラー",       29960,   19576),
    ("ＪＲ九州",           28352,    6864),
]
jp_nisa_growth = [
    ("キヤノン",          434000,  -53300),
    ("三菱商事(NISA)",    440900,  180800),
    ("Ｅギャランティ(N)", 369000,  111800),
    ("ＮＴＴ(NISA)",     516600,  -78400),
]
jp_old_nisa = [("信越化学", 732000, 303700)]

jp_stock_total  = 13877496 + 1760500 + 732000
jp_stock_profit = 6108046  + 160900  + 303700
jp_stock_cost   = jp_stock_total - jp_stock_profit

jp_funds = [
    ("eMAXIS Slim\nオールカントリー\n（成長投資枠）", 4301385, 1188621, 3112764),
    ("eMAXIS Slim\nオールカントリー\n（つみたて枠）",  3400168, 1100128, 2300040),
]
jp_fund_total  = 4301385 + 3400168
jp_fund_profit = 1188621 + 1100128

us_tokutei = [
    ("VTI",    180, 211.55, 372.69, 10827390, 6588570),
    ("HDV",    750,  19.42,  27.70,  3353085, 1732335),
    ("SPYD",   100,  40.32,  48.34,   780208,  331508),
    ("AMBQ",    80,  34.98,  85.28,  1101135,  685615),
]
us_nisa = [
    ("HDV(NISA)", 440, 21.86, 27.70, 1967143, 545063),
    ("PLTR",        7, 72.00,126.79,  143247,   66205),
]
us_old_nisa = [("SKYT", 450, 5.39, 32.54, 2363380, 2001130)]
us_tokutei_total  = 16061818; us_tokutei_profit = 9338028
us_nisa_total     = 2110390;  us_nisa_profit    = 611268
us_old_nisa_total = 2363380;  us_old_nisa_profit = 2001130
us_stock_total    = us_tokutei_total + us_nisa_total + us_old_nisa_total
us_stock_profit   = us_tokutei_profit + us_nisa_profit + us_old_nisa_profit

us_bonds = [
    ("4.125% 2027/9満期",   12717.44, 2052721),
    ("4.750% 2053/11満期",  13178.10, 2127077),
    ("4.250% 2035/8満期",    3900.00,  629499),
    ("4.000% 2035/11満期",  14626.28, 2360827),
]
us_bond_total = 7170124

sbi_usd_cash   = 1_880_000
sbi_jpy_cash   = 1_200_000
SBI_CASH_TOTAL = sbi_usd_cash + sbi_jpy_cash

GRAND_TOTAL  = jp_stock_total + jp_fund_total + us_stock_total + us_bond_total + SBI_CASH_TOTAL
GRAND_PROFIT = jp_stock_profit + jp_fund_profit + us_stock_profit
LOSS_RATE    = GRAND_PROFIT / (GRAND_TOTAL - GRAND_PROFIT - SBI_CASH_TOTAL) * 100

# ── ヘルパー ─────────────────────────────────────────────────────
_PN = [0]

def new_page(label='', title='', insight=''):
    _PN[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)
    if label:
        fig.text(0.04, 0.935, label, fontsize=9.5, color=TEXT2, va='center')
    if title:
        fig.text(0.04, 0.885, title, fontsize=16, color=TEXT,
                 fontweight='bold', va='center')
    if insight:
        fig.text(0.04, 0.840, insight, fontsize=9.5, color=TEXT2, va='center')
    d = fig.add_axes([0.04, 0.822, 0.92, 0.002])
    d.set_facecolor(BORDER); d.axis('off')
    f = fig.add_axes([0, 0, 1, 0.075])
    f.set_facecolor(FOOTER); f.axis('off')
    f.set_xlim(0,1); f.set_ylim(0,1)
    f.text(0.04, 0.45, '個人投資ポートフォリオ  SBI証券  2026年7月11日',
           color='#909090', fontsize=8, va='center')
    f.text(0.96, 0.45, str(_PN[0]), color='#D0D0D0', fontsize=11,
           fontweight='bold', ha='right', va='center')
    return fig

def gs_body(fig, nrows=1, ncols=2, hspace=0.42, wspace=0.28,
            top=0.810, bottom=0.105):
    return GridSpec(nrows, ncols, figure=fig,
                    left=0.04, right=0.97,
                    bottom=bottom, top=top,
                    hspace=hspace, wspace=wspace)

def cstyle(ax, title='', ylabel='', hgrid=True):
    ax.set_facecolor(BG)
    if hgrid:
        ax.yaxis.grid(True, color='#C8C4BE', lw=0.6, zorder=0)
    ax.xaxis.grid(False)
    ax.spines['bottom'].set_color('#C0BCB8'); ax.spines['bottom'].set_lw(0.8)
    ax.spines[['top','right','left']].set_visible(False)
    ax.tick_params(length=0, labelsize=9.5, colors=TEXT2)
    if title:
        ax.set_title(title, fontsize=11, fontweight='bold',
                     color=TEXT, pad=9, loc='left')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=TEXT2)

def mtable(ax, headers, rows, col_w=None, fs=9.0, rs=1.6):
    kw = dict(cellText=rows, colLabels=headers, cellLoc='center', loc='center')
    if col_w: kw['colWidths'] = col_w
    t = ax.table(**kw)
    t.auto_set_font_size(False)
    t.set_fontsize(fs)
    t.scale(1, rs)
    for (r,c), cell in t.get_celld().items():
        cell.set_linewidth(0.4)
        if r == 0:
            cell.set_facecolor(HDRBG)
            cell.set_edgecolor('#B8B4B0')
            cell.get_text().set_color(TEXT)
            cell.get_text().set_fontweight('bold')
        elif r % 2 == 0:
            cell.set_facecolor(ALTBG); cell.set_edgecolor('#D0CCC8')
        else:
            cell.set_facecolor(BG); cell.set_edgecolor('#D0CCC8')
    ax.axis('off'); return t

def blbls(ax, bars, suffix='万', frac=0.04):
    mx = max(b.get_height() for b in bars) if bars else 1
    for b in bars:
        h = b.get_height()
        if abs(h) < 0.001: continue
        ax.text(b.get_x()+b.get_width()/2, h+mx*frac,
                f'{h:.1f}{suffix}', ha='center', va='bottom',
                fontsize=8.5, fontweight='bold', color=TEXT)

# ════════════════════════════════════════════════════════════════
# 1. 表紙
# ════════════════════════════════════════════════════════════════
def s1_cover():
    _PN[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)

    left = fig.add_axes([0, 0.12, 0.40, 0.78])
    left.set_facecolor(TEAL); left.axis('off')

    fig.text(0.46, 0.80, '保有証券', fontsize=30, fontweight='bold', color=TEXT)
    fig.text(0.46, 0.70, 'ポートフォリオ分析', fontsize=26, fontweight='bold', color=TEXT)
    fig.text(0.46, 0.61, 'SBI証券  ／  2026年7月11日 時点', fontsize=12, color=TEXT2)

    kpis = [
        (f"{GRAND_TOTAL/1e8:.2f}億円", '総資産評価額',   TEAL),
        (f"+{GRAND_PROFIT/1e4:.0f}万円",'総評価益',     POS),
        (f"+{LOSS_RATE:.1f}%",          '損益率（投資部分）', POS),
        ("日本28 ＋ 米国7",             '保有銘柄数',    BLUE1),
    ]
    for i,(val,lbl,clr) in enumerate(kpis):
        ky = 0.48 - i*0.085
        fig.text(0.46, ky, val, fontsize=15, fontweight='bold', color=clr, va='center')
        fig.text(0.68, ky, lbl, fontsize=10, color=TEXT2, va='center')

    d = fig.add_axes([0.46, 0.085, 0.50, 0.002])
    d.set_facecolor(BORDER); d.axis('off')
    fig.text(0.46, 0.057, '日本株 ・ 米国株 ・ 投資信託 ・ 米国国債  ｜  SBI証券 特定・NISA・旧NISA',
             fontsize=9, color=TEXT2)

    f = fig.add_axes([0,0,1,0.075])
    f.set_facecolor(FOOTER); f.axis('off')
    f.set_xlim(0,1); f.set_ylim(0,1)
    f.text(0.5, 0.45, '個人投資ポートフォリオ  SBI証券  2026年7月11日',
           ha='center', color='#909090', fontsize=8, va='center')
    f.text(0.96, 0.45, '1', color='#D0D0D0', fontsize=11, fontweight='bold',
           ha='right', va='center')
    return fig

# ════════════════════════════════════════════════════════════════
# 2. ポートフォリオ全体概要
# ════════════════════════════════════════════════════════════════
def s2_overview():
    fig = new_page(
        label='ポートフォリオ全体概要',
        title='ポートフォリオ全体概要',
        insight=f"総評価額: {GRAND_TOTAL/1e8:.2f}億円  ／  総評価益: +{GRAND_PROFIT/1e4:.0f}万円  ／  損益率: +{LOSS_RATE:.1f}%（投資部分）"
    )
    gs = gs_body(fig, 1, 2, wspace=0.30)

    # 左: アセット配分 円グラフ
    ax1 = fig.add_subplot(gs[0,0])
    ax1.set_facecolor(BG)
    labels = ['日本株\n(特定・NISA)','日本\n投資信託','米国株\n(特定・NISA)','米国\n国債','SBI\n預り金']
    sizes  = [jp_stock_total, jp_fund_total, us_stock_total, us_bond_total, SBI_CASH_TOTAL]
    pcolors= [BLUE1, POS, AMBER, PURPLE, TEAL]
    wedges, texts, autos = ax1.pie(
        sizes, labels=labels, colors=pcolors,
        autopct='%1.1f%%', startangle=140,
        textprops={'fontsize':9.5},
        wedgeprops={'linewidth':2,'edgecolor':BG},
        explode=[0.03]*5
    )
    for at in autos: at.set_fontsize(9); at.set_fontweight('bold')
    ax1.set_title('アセット配分', fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')

    # 右: 口座別棒グラフ
    ax2 = fig.add_subplot(gs[0,1])
    blbls_labels = ['日本株\n特定','日本株\nNISA','日本株\n旧NISA',
                    '投信\n成長枠','投信\nつみたて',
                    '米国株\n特定','米国株\nNISA','米国株\n旧NISA','米国\n国債','SBI\n預り金']
    bvals = [jp_stock_total-1760500-732000, 1760500, 732000,
             4301385, 3400168,
             us_tokutei_total, us_nisa_total, us_old_nisa_total,
             us_bond_total, SBI_CASH_TOTAL]
    bclrs = [BLUE1,'#7AC0E0','#A8D8EE', POS,'#5DBF7A',
             AMBER,'#E8A050','#E8C878', PURPLE, TEAL]
    bars = ax2.bar(range(len(blbls_labels)), [v/1e6 for v in bvals],
                   color=bclrs, edgecolor=BG, linewidth=0.8, width=0.70, zorder=3)
    ax2.set_xticks(range(len(blbls_labels)))
    ax2.set_xticklabels(blbls_labels, fontsize=8)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}M'))
    for b, v in zip(bars, bvals):
        ax2.text(b.get_x()+b.get_width()/2, b.get_height()+0.05,
                 f'{v/1e6:.1f}M', ha='center', fontsize=7.5, fontweight='bold', color=TEXT)
    cstyle(ax2, '口座別 評価額（百万円）')
    return fig

# ════════════════════════════════════════════════════════════════
# 3. 日本株 評価額ランキング
# ════════════════════════════════════════════════════════════════
def s3_jp_ranking():
    all_s = jp_tokutei + jp_nisa_growth + jp_old_nisa
    srt_v = sorted(all_s, key=lambda x: x[1], reverse=True)
    srt_p = sorted(all_s, key=lambda x: x[2], reverse=True)

    fig = new_page(
        label='日本株 保有銘柄',
        title='日本株 保有銘柄 評価額ランキング',
        insight=f"特定22 ＋ NISA成長4 ＋ 旧NISA1  ｜  合計: {jp_stock_total/1e4:.0f}万円  ｜  評価益: +{jp_stock_profit/1e4:.0f}万円"
    )
    gs = gs_body(fig, 1, 2, wspace=0.35)

    # 左: 評価額ランキング
    ax1 = fig.add_subplot(gs[0,0])
    ns  = [s[0] for s in srt_v]
    vs  = [s[1]/1e4 for s in srt_v]
    ps  = [s[2] for s in srt_v]
    clrs = [TEAL if i<3 else BLUE1 for i in range(len(ns))]
    bars = ax1.barh(range(len(ns)), vs, color=clrs,
                    edgecolor=BG, height=0.68, lw=0.7, zorder=3)
    ax1.set_yticks(range(len(ns))); ax1.set_yticklabels(ns, fontsize=8.5)
    ax1.invert_yaxis()
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    mv = max(vs)
    for b, v, p in zip(bars, vs, ps):
        sign = '+' if p>=0 else ''
        clr  = POS if p>=0 else NEG
        ax1.text(b.get_width()+mv*0.02, b.get_y()+b.get_height()/2,
                 f'{v:.0f}万  {sign}{p/1e4:.1f}万',
                 va='center', fontsize=7.5, color=clr)
    ax1.set_xlim(0, mv*1.50)
    ax1.xaxis.grid(True, color=BORDER, lw=0.6, zorder=0)
    ax1.yaxis.grid(False)
    ax1.set_facecolor(BG)
    ax1.spines['bottom'].set_color('#C0BCB8'); ax1.spines['bottom'].set_lw(0.8)
    ax1.spines[['top','right','left']].set_visible(False)
    ax1.tick_params(length=0, labelsize=8.5, colors=TEXT2)
    ax1.set_title('全銘柄 評価額（万円）', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')

    # 右: 損益ランキング（上位15）
    ax2 = fig.add_subplot(gs[0,1])
    ns2  = [s[0] for s in srt_p[:15]]
    vs2  = [s[2]/1e4 for s in srt_p[:15]]
    clrs2 = [POS if v>=0 else NEG for v in vs2]
    ax2.barh(range(len(ns2)), vs2, color=clrs2,
             edgecolor=BG, height=0.65, lw=0.7, zorder=3)
    ax2.set_yticks(range(len(ns2))); ax2.set_yticklabels(ns2, fontsize=8.5)
    ax2.invert_yaxis()
    ax2.axvline(0, color=BORDER, lw=1)
    ax2.xaxis.grid(True, color=BORDER, lw=0.6, zorder=0)
    ax2.yaxis.grid(False)
    ax2.set_facecolor(BG)
    ax2.spines['bottom'].set_color('#C0BCB8'); ax2.spines['bottom'].set_lw(0.8)
    ax2.spines[['top','right','left']].set_visible(False)
    ax2.tick_params(length=0, labelsize=8.5, colors=TEXT2)
    ax2.set_title('損益 上位15銘柄（万円）', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 4. 日本株 セクター分析
# ════════════════════════════════════════════════════════════════
def s4_jp_sector():
    sectors = {
        '金融':        1342868+265746+369000+1093261+30019+119104+136962+553500+369000,
        '商社':        1968192+678986+440900+197820,
        '通信':        1228770+516600+591586+29960,
        '化学・素材':  1178980+732000,
        '人材・サービス': 1852880+56658+41400+28352,
        'その他':      567765+108480+1437207+434000,
    }
    scolors = [TEAL, BLUE1, '#7AC0E0', AMBER, POS, PURPLE]

    fig = new_page(
        label='日本株 セクター別分析',
        title='日本株 セクター別分析',
        insight='特定預り・NISA・旧NISA合算  ｜  金融・商社・通信が主力3セクター'
    )
    gs = gs_body(fig, 1, 2, wspace=0.30)

    ax1 = fig.add_subplot(gs[0,0])
    ax1.set_facecolor(BG)
    wedges, texts, autos = ax1.pie(
        list(sectors.values()), labels=list(sectors.keys()),
        colors=scolors, autopct='%1.1f%%', startangle=100,
        textprops={'fontsize':10}, wedgeprops={'linewidth':2,'edgecolor':BG},
        explode=[0.04]*len(sectors)
    )
    for at in autos: at.set_fontsize(9.5); at.set_fontweight('bold')
    ax1.set_title('セクター構成', fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')

    ax2 = fig.add_subplot(gs[0,1])
    ns2 = list(sectors.keys())
    vs2 = [v/1e4 for v in sectors.values()]
    bars = ax2.barh(range(len(ns2)), vs2, color=scolors,
                    edgecolor=BG, height=0.60, lw=0.7, zorder=3)
    ax2.set_yticks(range(len(ns2))); ax2.set_yticklabels(ns2, fontsize=10.5)
    ax2.invert_yaxis()
    ax2.xaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    mv2 = max(vs2)
    for b,v in zip(bars,vs2):
        ax2.text(b.get_width()+mv2*0.025, b.get_y()+b.get_height()/2,
                 f'{v:.0f}万', va='center', fontsize=9, fontweight='bold', color=TEXT)
    ax2.set_xlim(0, mv2*1.28)
    ax2.xaxis.grid(True, color=BORDER, lw=0.6, zorder=0)
    ax2.yaxis.grid(False)
    ax2.set_facecolor(BG)
    ax2.spines['bottom'].set_color('#C0BCB8'); ax2.spines['bottom'].set_lw(0.8)
    ax2.spines[['top','right','left']].set_visible(False)
    ax2.tick_params(length=0, labelsize=10.5, colors=TEXT2)
    ax2.set_title('セクター別 評価額（万円）', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 5. 日本株 NISA口座
# ════════════════════════════════════════════════════════════════
def s5_jp_nisa():
    fig = new_page(
        label='日本株 NISA口座',
        title='日本株 NISA口座 保有状況',
        insight='NISA成長投資枠 4銘柄（176.1万円 ｜ +16.1万）  ／  旧NISA 1銘柄（73.2万円 ｜ +30.4万）'
    )
    gs = gs_body(fig, 2, 1, hspace=0.50)

    # 上段: テーブル
    ax1 = fig.add_subplot(gs[0,0])
    ax1.set_title('保有銘柄 一覧', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')
    hdrs  = ['銘柄', '口座種別', '保有株数', '取得単価', '現在値', '評価額', '評価損益']
    rows  = [
        ('キヤノン',        'NISA成長', '100株',   '4,873円', '4,340円', '434,000円', '▲53,300円'),
        ('三菱商事',        'NISA成長', '100株',   '2,601円', '4,409円', '440,900円', '+180,800円'),
        ('Eギャランティ',   'NISA成長', '200株',   '1,286円', '1,845円', '369,000円', '+111,800円'),
        ('NTT',             'NISA成長', '3,500株', '170円',   '147円',   '516,600円', '▲78,400円'),
        ('信越化学',        '旧NISA',   '100株',   '4,283円', '7,320円', '732,000円', '+303,700円'),
        ('合　計',          '',         '',         '',        '',        '2,492,500円','＋464,600円'),
    ]
    cw = [0.18,0.13,0.10,0.11,0.11,0.145,0.145]
    t = mtable(ax1, hdrs, rows, col_w=cw, fs=9.0, rs=1.75)
    # 損益列に色付け
    for (r,c), cell in t.get_celld().items():
        if r > 0 and c == 6:
            txt = cell.get_text().get_text()
            if '+' in txt: cell.get_text().set_color(POS)
            elif '▲' in txt: cell.get_text().set_color(NEG)
            cell.get_text().set_fontweight('bold')

    # 下段: ポイント
    ax2 = fig.add_subplot(gs[1,0])
    ax2.set_facecolor(BG); ax2.axis('off')
    ax2.set_xlim(0,1); ax2.set_ylim(0,1)
    ax2.set_title('保有ポイント', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left',
                   transform=ax2.transAxes)
    pts = [
        (TEAL,  '信越化学（旧NISA）+70.9%',
         '半導体材料需要増により大幅上昇。旧NISAで非課税保有。'),
        (BLUE1, '三菱商事（NISA）+69.5%',
         'NISA口座で+180,800円。資源価格上昇の恩恵を享受。'),
        (NEG,   'NTT・キヤノン 含み損',
         '配当利回り目的で継続保有。長期では回収見込み。'),
    ]
    for i,(clr,title,desc) in enumerate(pts):
        iy = 0.80 - i*0.30
        ax2.add_patch(Rectangle((0.02, iy-0.02), 0.006, 0.22,
                                  color=clr, transform=ax2.transAxes))
        ax2.text(0.045, iy+0.13, title, fontsize=10, fontweight='bold',
                 color=clr, transform=ax2.transAxes)
        ax2.text(0.045, iy+0.04, desc, fontsize=9, color=TEXT2, transform=ax2.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════
# 6. 日本 投資信託
# ════════════════════════════════════════════════════════════════
def s6_jp_fund():
    fig = new_page(
        label='日本 投資信託',
        title='日本 投資信託（eMAXIS Slim オールカントリー）',
        insight=f"NISA成長投資枠 ＋ つみたて投資枠  ｜  合計評価額: {jp_fund_total/1e4:.0f}万円  ／  評価益: +{jp_fund_profit/1e4:.0f}万円"
    )
    gs = gs_body(fig, 1, 2, wspace=0.35)

    first_ax = None
    for i, (name, val, profit, cost) in enumerate(jp_funds):
        ax = fig.add_subplot(gs[0,i])
        if first_ax is None: first_ax = ax
        ax.set_facecolor(BG)
        rate = profit / cost * 100
        wedges, _, autos = ax.pie(
            [cost, profit], colors=[BLUE2, POS],
            autopct='%1.1f%%', startangle=90,
            wedgeprops={'linewidth':2,'edgecolor':BG},
            textprops={'fontsize':10}
        )
        for at in autos: at.set_fontsize(10); at.set_fontweight('bold')
        short = name.replace('\n',' ')
        ax.set_title(f'{short}\n評価額: {val/1e4:.0f}万円  (+{rate:.1f}%)',
                     fontsize=10, fontweight='bold', color=TEXT, pad=8, loc='left')

    if first_ax is not None:
        first_ax.legend(handles=[mpatches.Patch(color=BLUE2, label='取得金額'),
                                  mpatches.Patch(color=POS,   label='評価益')],
                        fontsize=9.5, loc='lower left', framealpha=0.9,
                        edgecolor=BORDER, fancybox=False)

    # ファンド比較テーブル（追加）
    # 下部に情報テーブルを足す
    ax_t = fig.add_axes([0.04, 0.08, 0.92, 0.12])
    ax_t.set_facecolor(BG); ax_t.axis('off')
    ax_t.set_xlim(0,1); ax_t.set_ylim(0,1)
    info = [
        ('ファンド名', 'eMAXIS Slim 全世界株式（オール・カントリー）'),
        ('口座',       'NISA成長投資枠 ／ つみたて投資枠'),
        ('合計取得額', f"{(jp_fund_total-jp_fund_profit)/1e4:.0f}万円"),
        ('合計評価額', f"{jp_fund_total/1e4:.0f}万円"),
        ('総評価益',   f"+{jp_fund_profit/1e4:.0f}万円  (+{jp_fund_profit/(jp_fund_total-jp_fund_profit)*100:.1f}%)"),
        ('分配金',     '再投資型（自動再投資）'),
    ]
    for i,(k,v) in enumerate(info):
        x = 0.01 + i*0.165
        ax_t.text(x, 0.78, k, fontsize=8.5, fontweight='bold', color=TEXT2)
        ax_t.text(x, 0.32, v, fontsize=8.5, color=TEXT)
    return fig

# ════════════════════════════════════════════════════════════════
# 7. 米国株
# ════════════════════════════════════════════════════════════════
def s7_us_stock():
    all_us = us_tokutei + us_nisa + us_old_nisa
    names  = [s[0] for s in all_us]
    vals   = [s[4]/1e6 for s in all_us]
    profs  = [s[5] for s in all_us]
    rates  = [s[5]/(s[4]-s[5])*100 if (s[4]-s[5])>0 else 0 for s in all_us]
    bclrs  = [AMBER]*4 + ['#E8A050']*2 + ['#D4AC0D']

    fig = new_page(
        label='米国株式 保有状況',
        title='米国株式 保有状況',
        insight=f"特定4 ＋ NISA2 ＋ 旧NISA1  ｜  円換算合計: {us_stock_total/1e4:.0f}万円  ／  評価益: +{us_stock_profit/1e4:.0f}万円"
    )
    gs = gs_body(fig, 1, 2, wspace=0.35)

    # 左: 評価額棒グラフ
    ax1 = fig.add_subplot(gs[0,0])
    xs = range(len(names))
    bars = ax1.bar(xs, vals, color=bclrs, edgecolor=BG, linewidth=0.8, width=0.70, zorder=3)
    ax1.set_xticks(xs)
    ax1.set_xticklabels(names, fontsize=9.5)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.1f}M'))
    for b, v, p in zip(bars, vals, profs):
        sign = '+' if p>=0 else ''; clr = POS if p>=0 else NEG
        ax1.text(b.get_x()+b.get_width()/2, b.get_height()+0.08,
                 f'{v:.1f}M\n{sign}{p/1e4:.0f}万',
                 ha='center', fontsize=8, fontweight='bold', color=clr)
    cstyle(ax1, '銘柄別 評価額（百万円）')
    ax1.legend(handles=[mpatches.Patch(color=AMBER,    label='特定預り'),
                        mpatches.Patch(color='#E8A050', label='NISA'),
                        mpatches.Patch(color='#D4AC0D', label='旧NISA')],
               fontsize=9, framealpha=0.9, edgecolor=BORDER, fancybox=False)

    # 右: 損益率
    ax2 = fig.add_subplot(gs[0,1])
    rclrs = [POS if r>0 else NEG for r in rates]
    ax2.barh(range(len(names)), rates, color=rclrs,
             edgecolor=BG, height=0.65, lw=0.7, zorder=3)
    ax2.set_yticks(range(len(names))); ax2.set_yticklabels(names, fontsize=9.5)
    ax2.invert_yaxis()
    ax2.axvline(0, color=BORDER, lw=1)
    for i, (r, b) in enumerate(zip(rates, ax2.patches)):
        sign = '+' if r>0 else ''
        clr  = POS if r>0 else NEG
        ax2.text(max(r+8, 8), b.get_y()+b.get_height()/2,
                 f'{sign}{r:.0f}%', va='center', fontsize=9,
                 fontweight='bold', color=clr)
    ax2.xaxis.grid(True, color=BORDER, lw=0.6, zorder=0)
    ax2.yaxis.grid(False)
    ax2.set_facecolor(BG)
    ax2.spines['bottom'].set_color('#C0BCB8'); ax2.spines['bottom'].set_lw(0.8)
    ax2.spines[['top','right','left']].set_visible(False)
    ax2.tick_params(length=0, labelsize=9.5, colors=TEXT2)
    ax2.set_title('銘柄別 損益率（%）', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 8. 米国債
# ════════════════════════════════════════════════════════════════
def s8_us_bond():
    bnames = [b[0] for b in us_bonds]
    busd   = [b[1] for b in us_bonds]
    bjpy   = [b[2] for b in us_bonds]
    bclrs  = [PURPLE,'#A080E8','#B898F0','#C0A8F0']
    xlbls  = ['2027\n(4.125%)','2053\n(4.750%)','2035/8\n(4.250%)','2035/11\n(4.000%)']

    fig = new_page(
        label='米ドル建て国債 保有状況',
        title='米ドル建て国債 保有状況',
        insight=f"特定預り 4本  ｜  円換算合計: {us_bond_total/1e4:.0f}万円  ／  為替レート 約157〜161円/USD"
    )
    gs = gs_body(fig, 1, 2, wspace=0.30)

    # 左: 棒グラフ
    ax1 = fig.add_subplot(gs[0,0])
    bars = ax1.bar(range(4), [j/1e4 for j in bjpy], color=bclrs,
                   edgecolor=BG, lw=0.8, width=0.60, zorder=3)
    ax1.set_xticks(range(4)); ax1.set_xticklabels(xlbls, fontsize=9.5)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    for b, j, u in zip(bars, bjpy, busd):
        ax1.text(b.get_x()+b.get_width()/2, b.get_height()+3,
                 f'{j/1e4:.0f}万\n(${u:,.0f})',
                 ha='center', fontsize=8.5, fontweight='bold', color=TEXT)
    cstyle(ax1, '満期別 評価額（円換算）')

    # 右: 構成比 円グラフ
    ax2 = fig.add_subplot(gs[0,1])
    ax2.set_facecolor(BG)
    wedges, texts, autos = ax2.pie(
        bjpy, labels=xlbls, colors=bclrs,
        autopct='%1.1f%%', startangle=90,
        textprops={'fontsize':9.5},
        wedgeprops={'linewidth':2,'edgecolor':BG},
        explode=[0.03]*4
    )
    for at in autos: at.set_fontsize(9); at.set_fontweight('bold')
    ax2.set_title('満期別 構成比', fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 9. 運用成績まとめ
# ════════════════════════════════════════════════════════════════
def s9_performance():
    categories = ['日本株\n（特定・NISA）', '日本\n投資信託', '米国株\n（全口座）']
    costs   = [jp_stock_cost, jp_fund_total-jp_fund_profit, us_stock_total-us_stock_profit]
    profits = [jp_stock_profit, jp_fund_profit, us_stock_profit]

    fig = new_page(
        label='運用成績まとめ',
        title='運用成績まとめ',
        insight=f"総評価額: {GRAND_TOTAL/1e8:.2f}億円  ／  総評価益: +{GRAND_PROFIT/1e4:.0f}万円  ／  損益率: +{LOSS_RATE:.1f}%（投資部分）"
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    # 左: 積み上げ棒グラフ
    ax1 = fig.add_subplot(gs[0,0])
    x = np.arange(len(categories))
    ax1.bar(x, [c/1e6 for c in costs], 0.55, label='取得金額', color=BLUE2,
            edgecolor=BG, lw=0.8, zorder=3)
    ax1.bar(x, [p/1e6 for p in profits], 0.55,
            bottom=[c/1e6 for c in costs], label='評価益', color=POS,
            edgecolor=BG, lw=0.8, zorder=3)
    ax1.set_xticks(x); ax1.set_xticklabels(categories, fontsize=10)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}M'))
    ax1.legend(fontsize=9.5, framealpha=0.9, edgecolor=BORDER, fancybox=False)
    for p, c in zip(profits, costs):
        rate = p/c*100
        ax1.text(list(x)[profits.index(p)], (c+p)/1e6+0.2,
                 f'+{rate:.0f}%', ha='center', fontsize=11.5,
                 fontweight='bold', color=POS)
    cstyle(ax1, '取得金額 vs 評価益（百万円）')

    # 右: サマリーテーブル
    ax2 = fig.add_subplot(gs[0,1])
    ax2.set_title('カテゴリ別 成績サマリー', fontsize=11, fontweight='bold',
                   color=TEXT, pad=9, loc='left')
    summary = [
        ('日本株（特定+NISA）', f"{jp_stock_total/1e4:.0f}万円",
         f"+{jp_stock_profit/1e4:.0f}万円",
         f"+{jp_stock_profit/jp_stock_cost*100:.0f}%"),
        ('日本 投資信託', f"{jp_fund_total/1e4:.0f}万円",
         f"+{jp_fund_profit/1e4:.0f}万円",
         f"+{jp_fund_profit/(jp_fund_total-jp_fund_profit)*100:.0f}%"),
        ('米国株（全口座）', f"{us_stock_total/1e4:.0f}万円",
         f"+{us_stock_profit/1e4:.0f}万円",
         f"+{us_stock_profit/(us_stock_total-us_stock_profit)*100:.0f}%"),
        ('米国国債', f"{us_bond_total/1e4:.0f}万円", '—', '安定運用'),
        ('SBI預り金\n（USD+円）', f"{SBI_CASH_TOTAL/1e4:.0f}万円", '—', 'USD188万+円120万'),
        ('合　計', f"{GRAND_TOTAL/1e8:.2f}億円",
         f"+{GRAND_PROFIT/1e4:.0f}万円",
         f"+{LOSS_RATE:.1f}%"),
    ]
    hdrs2 = ['カテゴリ', '評価額', '評価益', '損益率']
    cw2   = [0.35, 0.22, 0.22, 0.21]
    t = mtable(ax2, hdrs2, summary, col_w=cw2, fs=9.0, rs=1.62)
    # 合計行を強調
    for (r,c), cell in t.get_celld().items():
        if r == len(summary):
            cell.set_facecolor(HDRBG)
            cell.get_text().set_fontweight('bold')
            cell.get_text().set_color(TEAL)
    return fig

# ════════════════════════════════════════════════════════════════
# 10. ポートフォリオの特徴
# ════════════════════════════════════════════════════════════════
def s10_features():
    fig = new_page(
        label='ポートフォリオの特徴と注目銘柄',
        title='ポートフォリオの特徴と注目銘柄'
    )
    gs = gs_body(fig, 2, 2, hspace=0.40, wspace=0.25,
                 top=0.810, bottom=0.105)

    features = [
        (gs[0,0], TEAL,  '分散投資',
         '日本株28銘柄＋米国株7銘柄＋投信＋国債の\n4資産に分散。地域・セクターをカバー。'),
        (gs[0,1], BLUE1, '高配当重視',
         'NTT・KDDI・オリックス・三菱商事など高配当株が中核。\n米国はHDV・SPYDの高配当ETFでインカムゲインを確保。'),
        (gs[1,0], AMBER, '成長株保有',
         'SKYT(+504%)・PLTR(+76%)など成長株を\nNISA口座で非課税保有。JAC・三井物産も大幅高。'),
        (gs[1,1], POS,   'NISA最大活用',
         '成長投資枠・つみたて投資枠・旧NISAをフル活用。\n非課税口座での利益最大化を実現。'),
    ]
    for spec, clr, title, desc in features:
        ax = fig.add_subplot(spec)
        ax.set_facecolor(ALTBG)
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
        ax.add_patch(Rectangle((0,0),1,1, facecolor=ALTBG,
                                edgecolor=clr, lw=2, transform=ax.transAxes))
        ax.add_patch(Rectangle((0,0.88),1,0.12, color=clr, transform=ax.transAxes))
        ax.text(0.5, 0.94, title, ha='center', va='center', fontsize=12,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
        ax.text(0.5, 0.50, desc, ha='center', va='center', fontsize=9.5,
                color=TEXT2, transform=ax.transAxes, linespacing=1.7)

    # 注目銘柄バー
    note = fig.add_axes([0.04, 0.078, 0.92, 0.022])
    note.set_facecolor(TEAL); note.axis('off')
    note.set_xlim(0,1); note.set_ylim(0,1)
    note.text(0.5, 0.5,
              '注目銘柄  |  SKYT +504%  ・  三井物産 +228%  ・  三菱UFJ +73%  ・  VTI +76%  ・  PLTR +76%  ・  信越化学 +71%',
              ha='center', va='center', fontsize=9, color=WHITE, fontweight='bold')
    return fig

# ── PDF出力 ────────────────────────────────────────────────────
OUT = "/Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri/output/portfolio_report_v2.pdf"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

slides = [s1_cover, s2_overview, s3_jp_ranking, s4_jp_sector,
          s5_jp_nisa, s6_jp_fund, s7_us_stock, s8_us_bond,
          s9_performance, s10_features]

A4W = int(297*150/25.4); A4H = int(210*150/25.4)
imgs = []
for i, fn in enumerate(slides):
    print(f"  {i+1}/{len(slides)}: {fn.__name__}")
    fig = fn()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    imgs.append(Image.open(buf).convert('RGB').resize((A4W,A4H), Image.LANCZOS))
    plt.close(fig)

imgs[0].save(OUT, save_all=True, append_images=imgs[1:], resolution=150)
print(f"\n✅  {OUT}  ({os.path.getsize(OUT)//1024} KB)")
