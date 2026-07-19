#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投資プラン提案書 v3 — design01.pdf スタイル（3口座: SBI + 楽天 + 現金）
出力: output/investment_plan_v3.pdf
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
jp_stock_total  = 12934193.5 + 1726200 + 731000
jp_stock_profit = 5827639.5  + 126600  + 302700
jp_fund_total   = 4253472 + 3362294
jp_fund_profit  = 1140708 + 1062254
us_stock_total  = 15952003 + 2061994 + 2656243
us_stock_profit = 9228213  + 562872  + 2293993
us_bond_total   = 7170124
SBI_CASH_TOTAL  = 3_080_000
SBI_PROFIT      = jp_stock_profit + jp_fund_profit + us_stock_profit
SBI_TOTAL       = jp_stock_total + jp_fund_total + us_stock_total + us_bond_total + SBI_CASH_TOTAL

rakuten_vti_val   = 7_190_827; rakuten_vti_cost  = 2_823_700
rakuten_spcx_val  =    89_527; rakuten_spcx_cost =    91_384
RAKUTEN_TOTAL  = rakuten_vti_val + rakuten_spcx_val
RAKUTEN_PROFIT = (rakuten_vti_val - rakuten_vti_cost) + (rakuten_spcx_val - rakuten_spcx_cost)
RAKUTEN_COST   = RAKUTEN_TOTAL - RAKUTEN_PROFIT

CASH          = 9_000_000
GRAND_TOTAL   = SBI_TOTAL + RAKUTEN_TOTAL + CASH
GRAND_PROFIT  = SBI_PROFIT + RAKUTEN_PROFIT
invest_base   = GRAND_TOTAL - CASH - us_bond_total - SBI_CASH_TOTAL
GRAND_RATE    = GRAND_PROFIT / (invest_base - GRAND_PROFIT) * 100

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
    f.text(0.04, 0.45, '個人投資プラン提案書  SBI証券 ／ 楽天証券  2026年6月19日',
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

def cstyle(ax, title='', ylabel=''):
    ax.set_facecolor(BG)
    ax.yaxis.grid(True, color=BORDER, lw=0.6, zorder=0)
    ax.xaxis.grid(False)
    ax.spines['bottom'].set_color('#C0BCB8'); ax.spines['bottom'].set_lw(0.8)
    ax.spines[['top','right','left']].set_visible(False)
    ax.tick_params(length=0, labelsize=9.5, colors=TEXT2)
    if title:
        ax.set_title(title, fontsize=11, fontweight='bold',
                     color=TEXT, pad=9, loc='left')
    if ylabel: ax.set_ylabel(ylabel, fontsize=9, color=TEXT2)

def mtable(ax, headers, rows, col_w=None, fs=9.0, rs=1.6):
    kw = dict(cellText=rows, colLabels=headers, cellLoc='center', loc='center')
    if col_w: kw['colWidths'] = col_w
    t = ax.table(**kw)
    t.auto_set_font_size(False); t.set_fontsize(fs); t.scale(1, rs)
    for (r,c), cell in t.get_celld().items():
        cell.set_linewidth(0.4)
        if r == 0:
            cell.set_facecolor(HDRBG); cell.set_edgecolor('#B8B4B0')
            cell.get_text().set_color(TEXT); cell.get_text().set_fontweight('bold')
        elif r % 2 == 0:
            cell.set_facecolor(ALTBG); cell.set_edgecolor('#D0CCC8')
        else:
            cell.set_facecolor(BG); cell.set_edgecolor('#D0CCC8')
    ax.axis('off'); return t

def plan_box(fig, pos, color, title, items, fs=9.0):
    """(left,bottom,width,height), color, title, list[(bullet,text)]"""
    ax = fig.add_axes(pos)
    ax.set_facecolor(ALTBG)
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
    ax.add_patch(Rectangle((0,0.88),1,0.12, color=color, transform=ax.transAxes))
    ax.text(0.5,0.94, title, ha='center', va='center',
            fontsize=11, fontweight='bold', color=WHITE, transform=ax.transAxes)
    step = 0.80 / max(len(items),1)
    for i,(bul,txt) in enumerate(items):
        y = 0.83 - i*step
        ax.text(0.04, y, f'● {bul}', fontsize=9.5, fontweight='bold',
                color=color, transform=ax.transAxes)
        ax.text(0.04, y-step*0.42, txt, fontsize=fs, color=TEXT2,
                transform=ax.transAxes, wrap=True)
    return ax

# ════════════════════════════════════════════════════════════════
# 1. 表紙
# ════════════════════════════════════════════════════════════════
def s1_cover():
    _PN[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)
    left = fig.add_axes([0, 0.12, 0.40, 0.78])
    left.set_facecolor(TEAL); left.axis('off')

    fig.text(0.46, 0.82, '投資プラン', fontsize=28, fontweight='bold', color=TEXT)
    fig.text(0.46, 0.73, '提案書', fontsize=28, fontweight='bold', color=TEXT)
    fig.text(0.46, 0.63, 'SBI証券 ／ 楽天証券 ／ 現金\n2026年6月19日 時点', fontsize=12, color=TEXT2)

    kpis = [
        (f"{GRAND_TOTAL/1e8:.3f}億円",    '総資産',            TEAL),
        (f"+{GRAND_PROFIT/1e4:.0f}万円",  '総評価益',          POS),
        (f"+{GRAND_RATE:.1f}%",           '投資部分 損益率',   POS),
        (f"{CASH/1e4:.0f}万円",           '現金（活用可能）',  AMBER),
    ]
    for i,(val,lbl,clr) in enumerate(kpis):
        ky = 0.50 - i*0.085
        fig.text(0.46, ky, val, fontsize=15, fontweight='bold', color=clr, va='center')
        fig.text(0.70, ky, lbl, fontsize=10, color=TEXT2, va='center')

    d = fig.add_axes([0.46, 0.088, 0.50, 0.002])
    d.set_facecolor(BORDER); d.axis('off')
    fig.text(0.46, 0.060, '3口座 統合管理  ｜  SBI証券  楽天証券  現金  ｜  最適配分プラン A/B/C/D 比較',
             fontsize=9, color=TEXT2)
    f = fig.add_axes([0,0,1,0.075])
    f.set_facecolor(FOOTER); f.axis('off')
    f.set_xlim(0,1); f.set_ylim(0,1)
    f.text(0.5,0.45,'個人投資プラン提案書  2026年6月19日',
           ha='center', color='#909090', fontsize=8, va='center')
    f.text(0.96,0.45,'1',color='#D0D0D0',fontsize=11,fontweight='bold',
           ha='right',va='center')
    return fig

# ════════════════════════════════════════════════════════════════
# 2. 全資産サマリー
# ════════════════════════════════════════════════════════════════
def s2_total_summary():
    labels = ['SBI\n日本株','SBI\n投信','SBI\n米国株','SBI\n国債',
              'SBI\n預り金','楽天\n証券','現金']
    vals   = [jp_stock_total, jp_fund_total, us_stock_total, us_bond_total,
              SBI_CASH_TOTAL, RAKUTEN_TOTAL, CASH]
    clrs   = [BLUE1, POS, AMBER, PURPLE, TEAL, '#E8A050', '#D0CCC8']
    pcats  = ['SBI証券','楽天証券','現金']
    pvals  = [SBI_TOTAL, RAKUTEN_TOTAL, CASH]
    pclrs  = [TEAL, AMBER, '#D0CCC8']

    fig = new_page(
        label='全資産サマリー',
        title='全資産サマリー（3口座合計）',
        insight=f"総資産: {GRAND_TOTAL/1e8:.3f}億円  ／  総評価益: +{GRAND_PROFIT/1e4:.0f}万円  ／  投資部分損益率: +{GRAND_RATE:.1f}%"
    )
    gs = gs_body(fig, 1, 2, wspace=0.30)

    # 左: 口座別比較棒グラフ
    ax1 = fig.add_subplot(gs[0,0])
    bars = ax1.bar(range(len(labels)), [v/1e6 for v in vals],
                   color=clrs, edgecolor=BG, lw=0.8, width=0.68, zorder=3)
    ax1.set_xticks(range(len(labels)))
    ax1.set_xticklabels(labels, fontsize=8.5)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}M'))
    for b,v in zip(bars,vals):
        ax1.text(b.get_x()+b.get_width()/2, b.get_height()+0.05,
                 f'{v/1e6:.1f}M', ha='center', fontsize=7.5,
                 fontweight='bold', color=TEXT)
    cstyle(ax1, '資産カテゴリ別 評価額（百万円）')

    # 右: 口座比率 円グラフ
    ax2 = fig.add_subplot(gs[0,1])
    ax2.set_facecolor(BG)
    wedges, texts, autos = ax2.pie(
        pvals, labels=pcats, colors=pclrs,
        autopct='%1.1f%%', startangle=90,
        textprops={'fontsize':11},
        wedgeprops={'linewidth':2,'edgecolor':BG},
        explode=[0.03]*3
    )
    for at in autos: at.set_fontsize(10.5); at.set_fontweight('bold')
    ax2.set_title('口座別 資産配分', fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')

    # KPIバー
    kpis = [
        ('SBI証券', f"{SBI_TOTAL/1e8:.2f}億円", f"+{SBI_PROFIT/1e4:.0f}万円", TEAL),
        ('楽天証券', f"{RAKUTEN_TOTAL/1e4:.0f}万円", f"+{RAKUTEN_PROFIT/1e4:.0f}万円", AMBER),
        ('現金',    f"{CASH/1e4:.0f}万円", '投資余力', '#808080'),
        ('合計',    f"{GRAND_TOTAL/1e8:.3f}億円", f"+{GRAND_PROFIT/1e4:.0f}万円", POS),
    ]
    kb = fig.add_axes([0.04, 0.075, 0.92, 0.030])
    kb.set_facecolor(FOOTER); kb.axis('off')
    kb.set_xlim(0,1); kb.set_ylim(0,1)
    for i,(nm,ev,ep,clr) in enumerate(kpis):
        x = 0.03 + i*0.250
        kb.text(x, 0.72, nm, fontsize=8, color='#A0A0A0', fontweight='bold')
        kb.text(x, 0.28, f'{ev}  {ep}', fontsize=9, color=WHITE, fontweight='bold')
    return fig

# ════════════════════════════════════════════════════════════════
# 3. 楽天証券 詳細
# ════════════════════════════════════════════════════════════════
def s3_rakuten():
    vti_rate  = (rakuten_vti_val  - rakuten_vti_cost)  / rakuten_vti_cost  * 100
    spcx_rate = (rakuten_spcx_val - rakuten_spcx_cost) / rakuten_spcx_cost * 100

    fig = new_page(
        label='楽天証券 保有状況',
        title='楽天証券 保有状況',
        insight=f"合計: {RAKUTEN_TOTAL/1e4:.0f}万円  ／  評価益: +{RAKUTEN_PROFIT/1e4:.0f}万円  ／  損益率: +{RAKUTEN_PROFIT/RAKUTEN_COST*100:.1f}%"
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    # 左: 棒グラフ (取得 vs 評価益)
    ax1 = fig.add_subplot(gs[0,0])
    cats  = ['楽天VTI', 'SPCX']
    costs = [rakuten_vti_cost, rakuten_spcx_cost]
    profs = [rakuten_vti_val - rakuten_vti_cost, rakuten_spcx_val - rakuten_spcx_cost]
    x = np.arange(2)
    ax1.bar(x, [c/1e4 for c in costs], 0.5, label='取得金額', color=BLUE2,
            edgecolor=BG, lw=0.8, zorder=3)
    ax1.bar(x, [p/1e4 for p in profs], 0.5,
            bottom=[c/1e4 for c in costs], label='評価益', color=POS,
            edgecolor=BG, lw=0.8, zorder=3)
    ax1.set_xticks(x); ax1.set_xticklabels(cats, fontsize=11)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    for xi, (c,p) in enumerate(zip(costs, profs)):
        rate = p/c*100
        ax1.text(xi, (c+p)/1e4+5, f'+{rate:.1f}%', ha='center',
                 fontsize=12, fontweight='bold', color=POS)
    ax1.legend(fontsize=9.5, framealpha=0.9, edgecolor=BORDER, fancybox=False)
    cstyle(ax1, '取得金額 vs 評価益（万円）')

    # 右: 詳細テーブル
    ax2 = fig.add_subplot(gs[0,1])
    rows = [
        ('楽天VTI', '全世界株式インデックス', f"{rakuten_vti_cost/1e4:.0f}万円",
         f"{rakuten_vti_val/1e4:.0f}万円", f"+{(rakuten_vti_val-rakuten_vti_cost)/1e4:.0f}万円",
         f"+{vti_rate:.1f}%"),
        ('SPCX',   'S&P500 除く中国',       f"{rakuten_spcx_cost/1e4:.1f}万円",
         f"{rakuten_spcx_val/1e4:.1f}万円",f"+{(rakuten_spcx_val-rakuten_spcx_cost)/1e4:.1f}万円",
         f"{spcx_rate:+.1f}%"),
        ('合計',   '',
         f"{RAKUTEN_COST/1e4:.0f}万円",
         f"{RAKUTEN_TOTAL/1e4:.0f}万円",
         f"+{RAKUTEN_PROFIT/1e4:.0f}万円",
         f"+{RAKUTEN_PROFIT/RAKUTEN_COST*100:.1f}%"),
    ]
    hdrs = ['銘柄', '分類', '取得金額', '評価額', '評価益', '損益率']
    cw   = [0.12, 0.24, 0.14, 0.14, 0.16, 0.12]
    t = mtable(ax2, hdrs, rows, col_w=cw, fs=9.0, rs=1.9)
    for (r,c), cell in t.get_celld().items():
        if c == 5 and r > 0:
            txt = cell.get_text().get_text()
            cell.get_text().set_color(POS if '+' in txt else NEG)
            cell.get_text().set_fontweight('bold')
        if r == len(rows):
            cell.set_facecolor(HDRBG)
            cell.get_text().set_color(TEAL); cell.get_text().set_fontweight('bold')
    ax2.set_title('楽天証券 保有明細', fontsize=11, fontweight='bold',
                   color=TEXT, pad=9, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 4. SWOT 分析
# ════════════════════════════════════════════════════════════════
def s4_swot():
    fig = new_page(
        label='ポートフォリオ SWOT分析',
        title='ポートフォリオ SWOT分析',
        insight='現状の強み・課題を整理し、今後の投資判断に活用'
    )
    quadrants = [
        (0.04, 0.44, 0.44, 0.37, POS,  '強み (Strengths)',
         ['分散投資', '日本株28銘柄・米国株7銘柄・投信・国債で4資産分散。地域・セクター幅広くカバー。',
          '高含み益', f"総評価益 +{GRAND_PROFIT/1e4:.0f}万円 (投資部分+{GRAND_RATE:.0f}%)。VTI・SKYT等が大幅高。",
          'NISA最大活用', '成長投資枠・つみたて枠・旧NISAをフル利用。非課税利益を最大化。']),
        (0.52, 0.44, 0.44, 0.37, AMBER, '弱み (Weaknesses)',
         ['集中リスク', 'VTI(米国株)が単一銘柄で総資産の16%超。コアETF依存度が高い。',
          '為替リスク', '米国株・国債の円換算額は為替に大きく左右される(USD資産約60%)。',
          '流動性', '国債4本は満期まで売却困難。長期(最長2053年)の固定金利。']),
        (0.04, 0.10, 0.44, 0.37, BLUE1, '機会 (Opportunities)',
         ['現金活用', f"現金{CASH/1e4:.0f}万円を優良ETF・高配当株・債券に段階投入可能。",
          '楽天拡充', 'NISA口座・ポイント投資を活用。年間投入余地あり。',
          '配当再投資', 'HDV・SPYD等の分配金を自動再投資し複利効果を拡大。']),
        (0.52, 0.10, 0.44, 0.37, NEG,  'リスク (Threats)',
         ['円高リスク', '1ドル=140円台になると米国資産の円換算が大幅下落する。',
          '米国株調整', 'AI・テック相場の過熱感。調整時はVTI・PLTRが大きく下落する可能性。',
          '金利上昇', '長期国債(2053年)は金利上昇時に時価が下落する逆相関リスク。']),
    ]
    for (lf,bt,wd,ht, clr, title, items) in quadrants:
        ax = fig.add_axes([lf, bt, wd, ht])
        ax.set_facecolor(ALTBG)
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
        ax.add_patch(Rectangle((0,1-0.13),1,0.13, color=clr, transform=ax.transAxes))
        ax.text(0.5, 0.94, title, ha='center', va='center',
                fontsize=11, fontweight='bold', color=WHITE, transform=ax.transAxes)
        step = 0.78 / len(items[::2])
        for i in range(0, len(items), 2):
            y = 0.82 - (i//2)*step
            ax.text(0.03, y, f'● {items[i]}', fontsize=9, fontweight='bold',
                    color=clr, transform=ax.transAxes)
            ax.text(0.03, y-step*0.38, items[i+1], fontsize=8.2, color=TEXT2,
                    transform=ax.transAxes, wrap=True)
    return fig

# ════════════════════════════════════════════════════════════════
# 5. 現金900万 活用プラン
# ════════════════════════════════════════════════════════════════
def s5_cash_plan():
    allocs = [
        (TEAL,   '高配当株 追加\n（日本・米国）', 300, '配当収入強化'),
        (BLUE1,  '楽天NISA\nつみたて追加', 200, '長期積立'),
        (AMBER,  '米国ETF\n（VIG/BND等）', 200, '分散強化'),
        (PURPLE, '米国国債\n（短期2026〜27）', 150, '安定運用'),
        ('#909090','緊急予備金\n（待機）', 150, '現金保持'),
    ]

    fig = new_page(
        label='現金900万 活用プラン',
        title='現金900万円 活用プラン（案）',
        insight='現金900万円を5分野に段階的に投資し、リスク分散と収益向上を目指す'
    )
    gs = gs_body(fig, 1, 2, wspace=0.30)

    # 左: 配分棒グラフ
    ax1 = fig.add_subplot(gs[0,0])
    names = [a[1].replace('\n',' ') for a in allocs]
    amts  = [a[2] for a in allocs]
    clrs  = [a[0] for a in allocs]
    bars  = ax1.barh(range(len(names)), amts, color=clrs,
                     edgecolor=BG, height=0.65, lw=0.7, zorder=3)
    ax1.set_yticks(range(len(names))); ax1.set_yticklabels(names, fontsize=9)
    ax1.invert_yaxis()
    for b, a, al in zip(bars, amts, allocs):
        ax1.text(b.get_width()+5, b.get_y()+b.get_height()/2,
                 f'{a}万円  ({al[3]})', va='center', fontsize=8.5,
                 fontweight='bold', color=TEXT)
    ax1.set_xlim(0, 420)
    ax1.xaxis.grid(True, color=BORDER, lw=0.6, zorder=0); ax1.yaxis.grid(False)
    ax1.set_facecolor(BG)
    ax1.spines['bottom'].set_color('#C0BCB8'); ax1.spines['bottom'].set_lw(0.8)
    ax1.spines[['top','right','left']].set_visible(False)
    ax1.tick_params(length=0, labelsize=9.5, colors=TEXT2)
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.set_title('配分案（万円）', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')

    # 右: 円グラフ
    ax2 = fig.add_subplot(gs[0,1])
    ax2.set_facecolor(BG)
    wedges, texts, autos = ax2.pie(
        amts, labels=[a[1] for a in allocs], colors=clrs,
        autopct='%1.0f%%', startangle=90,
        textprops={'fontsize':9},
        wedgeprops={'linewidth':2,'edgecolor':BG},
        explode=[0.03]*len(allocs)
    )
    for at in autos: at.set_fontsize(9.5); at.set_fontweight('bold')
    ax2.set_title('現金活用 配分比率', fontsize=11, fontweight='bold',
                   color=TEXT, pad=10, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 6. プランA — 守り重視
# ════════════════════════════════════════════════════════════════
def s6_plan_a():
    fig = new_page(
        label='プランA',
        title='プランA：守り重視（インカム強化）',
        insight='現金900万円を高配当株・国債・短期債に配分。配当収入を年間最大化し資産を安定運用'
    )
    gs = gs_body(fig, 2, 3, hspace=0.40, wspace=0.28, top=0.810, bottom=0.105)

    items = [
        (gs[0,0], TEAL,  '高配当株追加\n（日本）',
         ['対象', 'NTT・KDDI・武田・三菱UFJ等', '追加投資', '200万円', '年間配当予想', '約8〜10万円']),
        (gs[0,1], AMBER, '米国高配当ETF追加',
         ['対象', 'HDV・SPYD・VYM追加', '追加投資', '200万円', '年間分配予想', '約10万円']),
        (gs[0,2], PURPLE,'米国国債 追加',
         ['対象', '2027〜2028満期 短期債', '追加投資', '150万円', '利率', '4.0〜4.5%/年']),
        (gs[1,0], BLUE1, '楽天NISA積立',
         ['対象', 'eMAXIS Slim 全世界', '月額', '3.3万円/月', '年間', '約40万円']),
        (gs[1,1], POS,   '現金保持',
         ['待機資金', '150万円', '用途', '調整時の追加投入', '目的', 'リスク対応余力']),
        (gs[1,2], '#909090','期待効果',
         ['年間配当', '+30万円以上', '安定性', '高（変動少）', 'リスク', '低〜中']),
    ]
    for spec, clr, title, kv_list in items:
        ax = fig.add_subplot(spec)
        ax.set_facecolor(ALTBG); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
        ax.add_patch(Rectangle((0,0.85),1,0.15, color=clr, transform=ax.transAxes))
        ax.text(0.5,0.925, title, ha='center', va='center',
                fontsize=9.5, fontweight='bold', color=WHITE, transform=ax.transAxes)
        for i in range(0,len(kv_list),2):
            y = 0.74 - (i//2)*0.23
            ax.text(0.06, y, kv_list[i],    fontsize=8.5, color=TEXT2,  transform=ax.transAxes)
            ax.text(0.06, y-0.11, kv_list[i+1], fontsize=9,   color=TEXT, fontweight='bold',
                    transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════
# 7. プランB — 積立継続
# ════════════════════════════════════════════════════════════════
def s7_plan_b():
    # 積立シミュレーション（年率5%）
    years  = list(range(0,11))
    init   = RAKUTEN_TOTAL + jp_fund_total
    mthly  = 33333  # 4万/月
    vals5  = [init + mthly*12*y * (((1+0.05)**(y+1)-1)/0.05 if y>0 else 1) for y in years]
    vals3  = [init + mthly*12*y * (((1+0.03)**(y+1)-1)/0.03 if y>0 else 1) for y in years]

    fig = new_page(
        label='プランB',
        title='プランB：積立継続（長期成長）',
        insight='楽天・SBI両NISAをフル活用。月3.3万の積立継続で10年後の資産増加をシミュレーション'
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    # 左: シミュレーション折れ線
    ax1 = fig.add_subplot(gs[0,0])
    ax1.plot(years, [v/1e6 for v in vals5], color=TEAL, lw=2.2,
             marker='o', markersize=5, label='年率5%', zorder=3)
    ax1.plot(years, [v/1e6 for v in vals3], color=BLUE2, lw=2.2,
             marker='s', markersize=4, ls='--', label='年率3%', zorder=3)
    ax1.set_xticks(years); ax1.set_xticklabels([f"{y}年後" for y in years], fontsize=8)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}M'))
    ax1.legend(fontsize=9.5, framealpha=0.9, edgecolor=BORDER, fancybox=False)
    cstyle(ax1, '積立 10年後シミュレーション（百万円）')

    # 右: 積立内訳テーブル
    ax2 = fig.add_subplot(gs[0,1])
    rows = [
        ('楽天VTI積立',    '楽天NISA つみたて', '33,333円/月',  '400,000円', '全世界株指数連動'),
        ('SBI投信積立',    'SBI NISA つみたて', '現行継続',      '約100,000円','eMAXIS Slim全世界'),
        ('現金→投信追加',  'SBI NISA成長投資枠', '一括 200万円', '2,000,000円','積立元本を増加'),
        ('楽天NISA成長枠', '新規活用',          '一括 120万円', '1,200,000円','高配当株または指数'),
        ('合計（1年）',    '',                  '',             '≈3,700,000円', ''),
    ]
    hdrs = ['内容', '口座', '月額/頻度', '年間投資額', '対象']
    cw   = [0.22, 0.20, 0.14, 0.18, 0.22]
    t = mtable(ax2, hdrs, rows, col_w=cw, fs=8.5, rs=1.55)
    for (r,c), cell in t.get_celld().items():
        if r == len(rows):
            cell.set_facecolor(HDRBG)
            cell.get_text().set_color(TEAL); cell.get_text().set_fontweight('bold')
    ax2.set_title('積立 年間計画', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 8. プランC — 攻め型
# ════════════════════════════════════════════════════════════════
def s8_plan_c():
    candidates = [
        ('NVDA', 'エヌビディア', 'AI半導体', 50, '高（成長）'),
        ('MSFT', 'マイクロソフト', 'クラウド/AI', 50, '中（安定成長）'),
        ('ASML', 'ASML', '半導体製造装置', 50, '高（周期）'),
        ('CONY', '超高配当ETF', '月次分配', 30, '中（安定）'),
        ('TSLA', 'テスラ', 'EV・AI', 30, '最高（投機）'),
        ('国内中小型', '日本成長株', '時価総額中小', 40, '高（国内）'),
    ]

    fig = new_page(
        label='プランC',
        title='プランC：攻め型（成長株追加）',
        insight='現金250万円を成長銘柄に集中投入。高リスク・高リターンを狙う上乗せポジション'
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    # 左: 候補銘柄バー（配分）
    ax1 = fig.add_subplot(gs[0,0])
    cnames = [f"{c[1]}\n({c[0]})" for c in candidates]
    camts  = [c[3] for c in candidates]
    cclrs  = [TEAL, BLUE1, BLUE2, AMBER, NEG, PURPLE]
    ax1.barh(range(len(cnames)), camts, color=cclrs,
             edgecolor=BG, height=0.65, lw=0.7, zorder=3)
    ax1.set_yticks(range(len(cnames))); ax1.set_yticklabels(cnames, fontsize=9)
    ax1.invert_yaxis()
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    for i, (c, amt) in enumerate(zip(candidates, camts)):
        ax1.text(amt+2, i, f'{amt}万  {c[4]}', va='center', fontsize=8.5, color=TEXT)
    ax1.set_xlim(0, 90)
    ax1.xaxis.grid(True, color=BORDER, lw=0.6, zorder=0); ax1.yaxis.grid(False)
    ax1.set_facecolor(BG)
    ax1.spines['bottom'].set_color('#C0BCB8'); ax1.spines['bottom'].set_lw(0.8)
    ax1.spines[['top','right','left']].set_visible(False)
    ax1.tick_params(length=0, labelsize=9, colors=TEXT2)
    ax1.set_title('候補銘柄 投資配分（万円）', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')

    # 右: 候補銘柄テーブル
    ax2 = fig.add_subplot(gs[0,1])
    rows = [(c[0], c[1], c[2], f"{c[3]}万円", c[4]) for c in candidates]
    rows.append(('合計', '', '', f"{sum(c[3] for c in candidates)}万円", ''))
    hdrs = ['銘柄', '名称', 'セクター', '投資額', 'リスク評価']
    cw   = [0.12, 0.22, 0.20, 0.14, 0.24]
    t = mtable(ax2, hdrs, rows, col_w=cw, fs=9.0, rs=1.52)
    for (r,c), cell in t.get_celld().items():
        if r == len(rows):
            cell.set_facecolor(HDRBG)
            cell.get_text().set_color(TEAL); cell.get_text().set_fontweight('bold')
        if c == 4 and r > 0:
            txt = cell.get_text().get_text()
            if '最高' in txt: cell.get_text().set_color(NEG)
            elif '高' in txt: cell.get_text().set_color(AMBER)
    ax2.set_title('候補銘柄 詳細', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 9. プランD — 円高対応
# ════════════════════════════════════════════════════════════════
def s9_plan_d():
    rates    = [130, 140, 150, 157, 160, 165, 170]
    us_jpy   = 20670240 + 7170124  # 米国株+国債 (base at 157)
    us_usd   = us_jpy / 157
    sim_vals = [us_usd * r / 1e6 for r in rates]

    fig = new_page(
        label='プランD',
        title='プランD：円高対応（為替シミュレーション）',
        insight='円高リスクに備え、短期的にUSD資産を一部円建て資産へシフト。為替感応度を低減'
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    # 左: 為替感応グラフ
    ax1 = fig.add_subplot(gs[0,0])
    ax1.plot(rates, sim_vals, color=AMBER, lw=2.5, marker='o', markersize=6, zorder=3)
    ax1.axvline(157, color=BORDER, lw=1.2, ls='--')
    ax1.text(157.5, max(sim_vals)*0.85, '現在\n157円', fontsize=9,
             color=TEXT2, va='center')
    ax1.fill_between(rates, sim_vals, alpha=0.15, color=AMBER)
    ax1.set_xticks(rates)
    ax1.set_xticklabels([f'{r}円' for r in rates], fontsize=9.5)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}M'))
    cstyle(ax1, '為替レート別 米国資産評価額（百万円）')

    # 右: 対応策テーブル
    ax2 = fig.add_subplot(gs[0,1])
    rows = [
        ('円高130円', '▲約800万円', '米国株売却部分あり', '段階的 売却（VTI 50株など）'),
        ('円高140円', '▲約500万円', '国債継続保有',       '楽天NISA 円建て追加'),
        ('円高150円', '▲約200万円', '様子見',             'ETF積立継続のみ'),
        ('現状157円', '基準',       '現状維持',           'プランA/B継続'),
        ('円安160円+', '+約150万円', '好調',              '追加投資の好機'),
    ]
    hdrs = ['為替シナリオ', '円換算差', 'USD資産方針', '円建て対応']
    cw   = [0.16, 0.15, 0.22, 0.35]
    t = mtable(ax2, hdrs, rows, col_w=cw, fs=8.5, rs=1.58)
    for (r,c), cell in t.get_celld().items():
        if r in (1,2,3) and c == 1:
            cell.get_text().set_color(NEG); cell.get_text().set_fontweight('bold')
        if r == 4 and c == 1:
            cell.set_facecolor('#F0EAE0')
        if r == 5 and c == 1:
            cell.get_text().set_color(POS); cell.get_text().set_fontweight('bold')
    ax2.set_title('為替シナリオ別 対応策', fontsize=11, fontweight='bold',
                   color=TEXT, pad=9, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 10. プラン比較マトリックス
# ════════════════════════════════════════════════════════════════
def s10_comparison():
    plans = ['プランA\n守り重視', 'プランB\n積立継続', 'プランC\n攻め型', 'プランD\n円高対応', '現金活用\n提案']
    axes_list = ['リターン\n期待値', 'リスク\n低さ', '流動性', '配当\n収入', '実行\n容易さ']
    scores = [
        [3, 5, 4, 5, 5],  # A
        [4, 4, 3, 3, 5],  # B
        [5, 2, 2, 3, 3],  # C
        [3, 5, 4, 2, 3],  # D
        [3, 4, 5, 4, 5],  # 現金活用
    ]
    pclrs = [TEAL, BLUE1, NEG, AMBER, POS]

    fig = new_page(
        label='プラン比較',
        title='投資プラン 総合比較',
        insight='5軸評価（1〜5点）で各プランの特性を可視化。複合実行も可能'
    )
    gs = gs_body(fig, 1, 2, wspace=0.38)

    # 左: レーダーチャート
    ax1 = fig.add_subplot(gs[0,0], polar=True)
    ax1.set_facecolor(BG)
    N   = len(axes_list)
    ang = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    ang += ang[:1]
    for i, (sc, clr) in enumerate(zip(scores, pclrs)):
        vals = sc + sc[:1]
        ax1.plot(ang, vals, color=clr, lw=2, label=plans[i].replace('\n',' '))
        ax1.fill(ang, vals, color=clr, alpha=0.06)
    ax1.set_thetagrids(np.degrees(ang[:-1]), axes_list, fontsize=9)
    ax1.set_rlabel_position(30)
    ax1.set_yticks([1,2,3,4,5])
    ax1.set_yticklabels(['1','2','3','4','5'], fontsize=7, color=TEXT2)
    ax1.set_ylim(0,5)
    ax1.grid(color=BORDER, lw=0.6)
    ax1.spines['polar'].set_color(BORDER)
    ax1.legend(fontsize=8.5, loc='lower left', bbox_to_anchor=(-0.28,-0.15),
               framealpha=0.9, edgecolor=BORDER, fancybox=False)
    ax1.set_title('5軸 レーダーチャート', fontsize=11, fontweight='bold',
                   color=TEXT, pad=30, loc='left')

    # 右: スコアテーブル
    ax2 = fig.add_subplot(gs[0,1])
    hdrs = ['プラン'] + axes_list + ['投資額']
    rows = []
    invest_amt = ['750万', '370万/年', '250万', '300万', '900万']
    for i, (p, sc) in enumerate(zip(plans, scores)):
        rows.append([p.replace('\n','')] + [str(s) for s in sc] + [invest_amt[i]])
    cw = [0.22,0.13,0.13,0.10,0.12,0.14,0.12]
    t  = mtable(ax2, hdrs, rows, col_w=cw, fs=8.8, rs=1.55)
    # スコア5を強調
    for (r,c), cell in t.get_celld().items():
        if r > 0 and 1 <= c <= 5:
            v = cell.get_text().get_text()
            if v == '5':
                cell.set_facecolor('#D8F5E0')
                cell.get_text().set_color(POS); cell.get_text().set_fontweight('bold')
            elif v == '2':
                cell.set_facecolor('#FAE0E0')
                cell.get_text().set_color(NEG)
    ax2.set_title('プラン別 評価スコア（1〜5）', fontsize=11, fontweight='bold',
                   color=TEXT, pad=9, loc='left')
    return fig

# ════════════════════════════════════════════════════════════════
# 11. アクションスケジュール (12ヶ月)
# ════════════════════════════════════════════════════════════════
def s11_timeline():
    months_labels = ['2026\n6月', '7月', '8月', '9月', '10月', '11月',
                     '12月', '2027\n1月', '2月', '3月', '4月', '5月']
    tasks = [
        (TEAL,  '現金→高配当株 200万円投入',  0, 3),
        (AMBER, '米国ETF（HDV追加）100万円',   1, 2),
        (BLUE1, '楽天NISA 積立継続（毎月）',   0, 11),
        (POS,   'SBI つみたてNISA 継続',       0, 11),
        (PURPLE,'米国国債 追加 150万円',        2, 4),
        (TEAL,  '成長株候補（プランC）検討',    3, 5),
        (AMBER, '為替監視・円高対応判断',       4, 11),
        (BLUE2, '年次ポートフォリオ見直し',    11, 11),
    ]

    fig = new_page(
        label='アクションスケジュール',
        title='2026年6月〜2027年5月 アクションスケジュール',
        insight='投資実行の優先順位と時系列を整理。月次で進捗を確認'
    )
    ax = fig.add_axes([0.04, 0.10, 0.92, 0.70])
    ax.set_facecolor(BG)
    ax.set_xlim(-0.5, 11.5)
    ax.set_ylim(-0.5, len(tasks)-0.5)
    ax.set_xticks(range(12))
    ax.set_xticklabels(months_labels, fontsize=9.5, color=TEXT2)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t[1] for t in tasks], fontsize=9.5, color=TEXT)
    ax.invert_yaxis()
    ax.xaxis.grid(True, color=BORDER, lw=0.6, zorder=0)
    ax.yaxis.grid(False)
    ax.spines['bottom'].set_color('#C0BCB8'); ax.spines['bottom'].set_lw(0.8)
    ax.spines[['top','right','left']].set_visible(False)
    ax.tick_params(length=0)

    for i, (clr, lbl, s, e) in enumerate(tasks):
        width = max(e-s, 0.4)
        rect  = mpatches.FancyBboxPatch(
            (s-0.25, i-0.32), width+0.5, 0.65,
            boxstyle='round,pad=0.05', linewidth=0,
            facecolor=clr, alpha=0.85
        )
        ax.add_patch(rect)
        mid = s + width/2
        ax.text(mid, i, lbl, ha='center', va='center',
                fontsize=8.5, color=WHITE, fontweight='bold')
    return fig

# ── PDF出力 ─────────────────────────────────────────────────────
OUT = "/Users/takahiroazuma/Desktop/kabu/claude/output/investment_plan_v3.pdf"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

slides = [s1_cover, s2_total_summary, s3_rakuten, s4_swot, s5_cash_plan,
          s6_plan_a, s7_plan_b, s8_plan_c, s9_plan_d,
          s10_comparison, s11_timeline]

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
