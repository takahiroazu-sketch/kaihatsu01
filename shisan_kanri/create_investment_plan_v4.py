#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投資プラン提案書 v4 — design01.pdf スタイル（v2内容 + v4デザイン）
出力: output/investment_plan_v4.pdf
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
RAKUTEN= '#BF0000'

# ── データ（v2と同一） ────────────────────────────────────────────
jp_stock_total  = 12934193.5 + 1726200 + 731000
jp_stock_profit = 5827639.5  + 126600  + 302700
jp_stock_cost   = jp_stock_total - jp_stock_profit
jp_fund_total   = 4253472 + 3362294
jp_fund_profit  = 1140708 + 1062254
jp_fund_cost    = jp_fund_total - jp_fund_profit
us_tokutei_total  = 15952003; us_tokutei_profit = 9228213
us_nisa_total     = 2061994;  us_nisa_profit    = 562872
us_old_nisa_total = 2656243;  us_old_nisa_profit = 2293993
us_stock_total    = us_tokutei_total + us_nisa_total + us_old_nisa_total
us_stock_profit   = us_tokutei_profit + us_nisa_profit + us_old_nisa_profit
us_bond_total     = 7170124
sbi_usd_cash      = 1_880_000; sbi_jpy_cash = 1_200_000
SBI_CASH_TOTAL    = sbi_usd_cash + sbi_jpy_cash
SBI_TOTAL         = jp_stock_total + jp_fund_total + us_stock_total + us_bond_total + SBI_CASH_TOTAL

rakuten_vti_val   = 7_190_827; rakuten_vti_profit  = 4_340_827; rakuten_vti_cost  = 2_850_000
rakuten_spcx_val  =    89_527; rakuten_spcx_profit =    24_616; rakuten_spcx_cost =    64_911
RAKUTEN_TOTAL     = rakuten_vti_val + rakuten_spcx_val
RAKUTEN_PROFIT    = rakuten_vti_profit + rakuten_spcx_profit
RAKUTEN_COST      = RAKUTEN_TOTAL - RAKUTEN_PROFIT

CASH          = 9_000_000
GRAND_TOTAL   = SBI_TOTAL + RAKUTEN_TOTAL + CASH
SBI_PROFIT    = jp_stock_profit + jp_fund_profit + us_stock_profit
GRAND_PROFIT  = SBI_PROFIT + RAKUTEN_PROFIT
GRAND_RATE    = GRAND_PROFIT / (GRAND_TOTAL - GRAND_PROFIT - us_bond_total - CASH - SBI_CASH_TOTAL) * 100

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
    f.text(0.04, 0.45, '個人投資プラン提案書  SBI証券 ／ 楽天証券  2026年6月21日',
           color='#909090', fontsize=8, va='center')
    f.text(0.96, 0.45, str(_PN[0]), color='#D0D0D0', fontsize=11,
           fontweight='bold', ha='right', va='center')
    return fig

def gs_body(fig, nrows=1, ncols=2, hspace=0.42, wspace=0.28, top=0.810, bottom=0.105):
    return GridSpec(nrows, ncols, figure=fig, left=0.04, right=0.97,
                    bottom=bottom, top=top, hspace=hspace, wspace=wspace)

def cstyle(ax, title=''):
    ax.set_facecolor(BG)
    ax.yaxis.grid(True, color=BORDER, lw=0.6, zorder=0); ax.xaxis.grid(False)
    ax.spines['bottom'].set_color('#C0BCB8'); ax.spines['bottom'].set_lw(0.8)
    ax.spines[['top','right','left']].set_visible(False)
    ax.tick_params(length=0, labelsize=9.5, colors=TEXT2)
    if title:
        ax.set_title(title, fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')

def mtable(ax, headers, rows, col_w=None, fs=9.0, rs=1.6):
    kw = dict(cellText=rows, colLabels=headers, cellLoc='center', loc='center')
    if col_w: kw['colWidths'] = col_w
    t = ax.table(**kw); t.auto_set_font_size(False); t.set_fontsize(fs); t.scale(1, rs)
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

def action_row(ax, op, clr, name, detail, y, h=0.092):
    ax.add_patch(FancyBboxPatch((0.02, y), 0.94, h,
        boxstyle='round,pad=0.008', lw=1.2, edgecolor=clr,
        facecolor=ALTBG, transform=ax.transAxes))
    ax.add_patch(Rectangle((0.02, y), 0.058, h, color=clr, transform=ax.transAxes))
    ax.text(0.049, y+h/2, op, ha='center', va='center', fontsize=8.5,
            fontweight='bold', color=WHITE, transform=ax.transAxes)
    ax.text(0.095, y+h*0.68, name, fontsize=9.5, fontweight='bold',
            color=TEXT, transform=ax.transAxes)
    ax.text(0.095, y+h*0.22, detail, fontsize=8.5, color=TEXT2, transform=ax.transAxes)

# ════════════════════════════════════════════════════════════════
# 1. 表紙
# ════════════════════════════════════════════════════════════════
def s1_cover():
    _PN[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27)); fig.patch.set_facecolor(BG)
    left = fig.add_axes([0, 0.12, 0.40, 0.78])
    left.set_facecolor(TEAL); left.axis('off')

    fig.text(0.46, 0.82, '投資プラン', fontsize=28, fontweight='bold', color=TEXT)
    fig.text(0.46, 0.73, '提案書', fontsize=28, fontweight='bold', color=TEXT)
    fig.text(0.46, 0.63, 'SBI証券 ／ 楽天証券 ／ 現金\n2026年6月21日 最新データ反映版',
             fontsize=12, color=TEXT2)
    kpis = [
        (f"{GRAND_TOTAL/1e8:.2f}億円",   '総資産（3口座合算）', TEAL),
        (f"+{GRAND_PROFIT/1e4:.0f}万円", '総含み益',           POS),
        (f"+{GRAND_RATE:.1f}%",          '投資部分 損益率',    POS),
        (f"{CASH/1e4:.0f}万円",          '現金（待機資金）',   AMBER),
    ]
    for i,(val,lbl,clr) in enumerate(kpis):
        ky = 0.50 - i*0.085
        fig.text(0.46, ky, val, fontsize=15, fontweight='bold', color=clr, va='center')
        fig.text(0.71, ky, lbl, fontsize=10, color=TEXT2, va='center')
    d = fig.add_axes([0.46, 0.088, 0.50, 0.002]); d.set_facecolor(BORDER); d.axis('off')
    fig.text(0.46, 0.060,
             'プランA: 守り重視  /  プランB: 積立継続  /  プランC: 攻め型  /  プランD: 円高対応  /  現金活用プラン',
             fontsize=9, color=TEXT2)
    f = fig.add_axes([0,0,1,0.075]); f.set_facecolor(FOOTER); f.axis('off')
    f.set_xlim(0,1); f.set_ylim(0,1)
    f.text(0.5,0.45,'個人投資プラン提案書  2026年6月21日',
           ha='center',color='#909090',fontsize=8,va='center')
    f.text(0.96,0.45,'1',color='#D0D0D0',fontsize=11,fontweight='bold',ha='right',va='center')
    return fig

# ════════════════════════════════════════════════════════════════
# 2. 全資産サマリー
# ════════════════════════════════════════════════════════════════
def s2_total_summary():
    fig = new_page(
        label='全資産サマリー',
        title='全資産サマリー（3口座合算）',
        insight=f"総資産: {GRAND_TOTAL/1e8:.2f}億円  ／  総含み益: +{GRAND_PROFIT/1e4:.0f}万円  ／  損益率: +{GRAND_RATE:.1f}%（投資部分）  ／  現金比率: {(CASH+SBI_CASH_TOTAL)/GRAND_TOTAL*100:.1f}%"
    )
    gs = gs_body(fig, 1, 2, wspace=0.30)

    # 左: 円グラフ
    ax1 = fig.add_subplot(gs[0,0]); ax1.set_facecolor(BG)
    labels = ['SBI\n日本株','SBI\n投信','SBI\n米国株','SBI\n国債','SBI\n預り金','楽天\nVTI','楽天\nSPCX','現金']
    sizes  = [jp_stock_total, jp_fund_total, us_stock_total, us_bond_total,
              SBI_CASH_TOTAL, rakuten_vti_val, rakuten_spcx_val, CASH]
    colors = [BLUE1, POS, AMBER, PURPLE, TEAL, RAKUTEN, '#FF8080', '#C0C0C0']
    wedges, texts, autos = ax1.pie(
        sizes, labels=labels, colors=colors,
        autopct=lambda p: f'{p:.1f}%' if p > 2 else '',
        startangle=120, textprops={'fontsize':8.5},
        wedgeprops={'linewidth':2,'edgecolor':BG}, explode=[0.02]*len(sizes))
    for at in autos: at.set_fontsize(8); at.set_fontweight('bold')
    ax1.set_title('全資産 アセット配分', fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')

    # 右: 積み上げ棒グラフ
    ax2 = fig.add_subplot(gs[0,1])
    cats   = ['SBI\n日本株','SBI\n投信','SBI\n米国株','SBI\n国債','SBI\n預り金','楽天\nVTI','楽天\nSPCX','現金']
    costs  = [jp_stock_cost, jp_fund_cost, us_stock_total-us_stock_profit,
              us_bond_total, SBI_CASH_TOTAL, rakuten_vti_cost, rakuten_spcx_cost, CASH]
    profs  = [jp_stock_profit, jp_fund_profit, us_stock_profit,
              0, 0, rakuten_vti_profit, rakuten_spcx_profit, 0]
    x = np.arange(len(cats))
    ax2.bar(x, [c/1e6 for c in costs], 0.65, color=colors, edgecolor=BG, alpha=0.65, label='取得金額', zorder=3)
    ax2.bar(x, [p/1e6 for p in profs], 0.65, bottom=[c/1e6 for c in costs],
            color=colors, edgecolor=BG, label='評価益', zorder=3)
    ax2.set_xticks(x); ax2.set_xticklabels(cats, fontsize=7.5)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}M'))
    for i,(p,c) in enumerate(zip(profs, costs)):
        if p > 0:
            ax2.text(i, (c+p)/1e6+0.1, f'+{p/c*100:.0f}%', ha='center',
                     fontsize=7.5, fontweight='bold', color=colors[i])
    ax2.legend(fontsize=9, framealpha=0.9, edgecolor=BORDER, fancybox=False)
    cstyle(ax2, '口座別 取得金額 vs 評価益（百万円）')

    # KPIバー
    kb = fig.add_axes([0.04, 0.075, 0.92, 0.030])
    kb.set_facecolor(FOOTER); kb.axis('off'); kb.set_xlim(0,1); kb.set_ylim(0,1)
    kpis = [('SBI証券', f"{SBI_TOTAL/1e4:.0f}万円", f"+{SBI_PROFIT/1e4:.0f}万", TEAL),
            ('楽天証券', f"{RAKUTEN_TOTAL/1e4:.0f}万円", f"+{RAKUTEN_PROFIT/1e4:.0f}万", '#FF8080'),
            ('現金',     f"{CASH/1e4:.0f}万円", '待機資金', '#C0C0C0'),
            ('合計',     f"{GRAND_TOTAL/1e8:.2f}億円", f"+{GRAND_PROFIT/1e4:.0f}万", POS)]
    for i,(nm,ev,ep,clr) in enumerate(kpis):
        x = 0.03 + i*0.250
        kb.text(x, 0.72, nm, fontsize=8, color='#A0A0A0', fontweight='bold')
        kb.text(x, 0.20, f'{ev}  {ep}', fontsize=9, color=WHITE, fontweight='bold')
    return fig

# ════════════════════════════════════════════════════════════════
# 3. 楽天証券
# ════════════════════════════════════════════════════════════════
def s3_rakuten():
    fig = new_page(
        label='楽天証券 ポートフォリオ詳細',
        title='楽天証券 ポートフォリオ詳細',
        insight=f"総評価額: {RAKUTEN_TOTAL/1e4:.0f}万円  ／  総含み益: +{RAKUTEN_PROFIT/1e4:.0f}万円  ／  参考為替: 161.31円/USD（06/20）"
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    # 左: ファンド3本比較
    ax1 = fig.add_subplot(gs[0,0])
    funds = ['SBI\neMAXIS Slim\n(成長枠)', 'SBI\neMAXIS Slim\n(つみたて)', '楽天\nVTI']
    f_costs = [3112764, 2300040, 2850000]
    f_profs = [1140708, 1062254, 4340827]
    f_clrs  = [BLUE1, BLUE2, RAKUTEN]
    x = np.arange(len(funds))
    ax1.bar(x, [c/1e4 for c in f_costs], 0.55, color=f_clrs, edgecolor=BG, alpha=0.65, label='取得金額', zorder=3)
    ax1.bar(x, [p/1e4 for p in f_profs], 0.55, bottom=[c/1e4 for c in f_costs],
            color=f_clrs, edgecolor=BG, label='評価益', zorder=3)
    ax1.set_xticks(x); ax1.set_xticklabels(funds, fontsize=8.5)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    for i,(p,c) in enumerate(zip(f_profs, f_costs)):
        ax1.text(i, (c+p)/1e4+5, f'+{p/c*100:.1f}%', ha='center',
                 fontsize=11, fontweight='bold', color=f_clrs[i])
    ax1.legend(fontsize=9.5, framealpha=0.9, edgecolor=BORDER, fancybox=False)
    cstyle(ax1, 'インデックスファンド 3本 比較（万円）')

    # 右: 保有銘柄テーブル + ポイント
    ax2 = fig.add_subplot(gs[0,1]); ax2.set_facecolor(BG); ax2.axis('off')
    ax2.set_xlim(0,1); ax2.set_ylim(0,1)
    ax2.set_title('保有銘柄 詳細', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')

    rows = [
        ('楽天・全米株式\nインデックスF', '特定', '1,600,273口',
         '17,809円', '44,935円', '719.1万円', '+434.1万\n(+152.3%)'),
        ('スペースX (SPCX)', '特定', '3株',
         '135.00 USD', '185.00 USD', '8.9万円', '+2.5万\n(+37.9%)'),
    ]
    hdrs = ['銘柄','口座','数量','取得単価','現在値','評価額','損益']
    cw   = [0.22,0.08,0.13,0.12,0.12,0.13,0.18]
    # テーブルをbboxで上部に固定し、下部の注目ポイントと重ならないようにする
    t = ax2.table(cellText=rows, colLabels=hdrs, colWidths=cw,
                  cellLoc='center', bbox=[0, 0.50, 1, 0.48])
    t.auto_set_font_size(False); t.set_fontsize(8.5); t.scale(1, 1.0)
    for (r,c), cell in t.get_celld().items():
        cell.set_linewidth(0.4)
        if r == 0:
            cell.set_facecolor(HDRBG); cell.set_edgecolor('#B8B4B0')
            cell.get_text().set_color(TEXT); cell.get_text().set_fontweight('bold')
        elif r % 2 == 0:
            cell.set_facecolor(ALTBG); cell.set_edgecolor('#D0CCC8')
        else:
            cell.set_facecolor(BG); cell.set_edgecolor('#D0CCC8')
    for (r,c), cell in t.get_celld().items():
        if r > 0 and c == 6:
            cell.get_text().set_color(POS); cell.get_text().set_fontweight('bold')

    pts = [
        (RAKUTEN, '楽天VTI  +152.3%',
         'SBI内VTI(特定160株 +75%)と合わせ全米株式に約1,900万円集中。要注意。'),
        (AMBER,   'スペースX (SPCX)  +37.9%',
         '宇宙産業・通信衛星リーダー。上場直後の成長株として継続保有。'),
    ]
    for i,(clr,title,desc) in enumerate(pts):
        y = 0.30 - i*0.24
        ax2.add_patch(FancyBboxPatch((0,y),1,0.20,
            boxstyle='round,pad=0.01',lw=1.5,edgecolor=clr,
            facecolor=ALTBG,transform=ax2.transAxes))
        ax2.text(0.03, y+0.143, f'● {title}', fontsize=9.5, fontweight='bold',
                 color=clr, transform=ax2.transAxes)
        ax2.text(0.03, y+0.060, desc, fontsize=8.2, color=TEXT2, transform=ax2.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════
# 4. SWOT 強み・課題
# ════════════════════════════════════════════════════════════════
def s4_swot():
    fig = new_page(
        label='全ポートフォリオ 強み・課題分析',
        title='全ポートフォリオ 強み・課題分析（統合版）',
        insight=f"総資産 {GRAND_TOTAL/1e8:.2f}億円  ／  総含み益 +{GRAND_PROFIT/1e4:.0f}万円  ／  現金・預り金比率 {(CASH+SBI_CASH_TOTAL)/GRAND_TOTAL*100:.1f}%"
    )
    strengths = [
        ('超高い含み益バッファー',
         f"総含み益+{GRAND_PROFIT/1e4:.0f}万円（+{GRAND_RATE:.0f}%）。急落局面でも心理的余裕がある"),
        ('現金・預り金1,208万円の余力',
         'SBI預り金308万＋SBI外現金900万円。投資機会・急落局面に即対応できる'),
        ('インデックス×個別株の2軸',
         '楽天VTI・SBI eMAXIS Slim・VTIで全市場に連動しつつ個別株で超過収益'),
        ('NISA非課税の活用',
         '成長・つみたて・旧NISAをフル活用。将来の非課税収益が積み上がっている'),
        ('3口座による分散管理',
         'SBI（日米株）・楽天（インデックス）で運用スタイルを分離できている'),
    ]
    challenges = [
        ('VTI系への集中リスク',
         '楽天VTI + SBI VTI(特定160株) = 約1,900万円。全体の28%超が集中'),
        ('米国資産の為替リスク',
         '米国株+債券+楽天SPCX = 約2,874万円。円高150円で約254万円相当の損失'),
        ('日銀利上げの継続',
         '1.0%到達後も追加利上げ見込み。NTT・KDDI等の高配当株に逆風'),
        ('現金の機会損失',
         'SBI外900万＋SBI預り金308万が低利運用。個人向け国債等で少なくとも0.5%以上狙える'),
        ('中東地政学リスク',
         'ホルムズ海峡リスク継続。原油輸入95%を中東依存の日本株に影響'),
    ]

    for col, (items, clr, side) in enumerate([
        (strengths, POS,  0.02),
        (challenges, NEG, 0.52),
    ]):
        for i,(title,desc) in enumerate(items):
            y = 0.73 - i*0.130
            lf = side
            ax = fig.add_axes([lf, y-0.01, 0.46, 0.115])
            ax.set_facecolor(ALTBG); ax.axis('off')
            ax.set_xlim(0,1); ax.set_ylim(0,1)
            ax.add_patch(Rectangle((0,0),0.008,1, color=clr, transform=ax.transAxes))
            mark = '✓' if col==0 else '!'
            ax.text(0.025, 0.70, f'{mark}  {title}', fontsize=9.5, fontweight='bold',
                    color=clr, transform=ax.transAxes)
            ax.text(0.025, 0.25, desc, fontsize=8.5, color=TEXT2, transform=ax.transAxes)

    fig.text(0.50, 0.135, '強み', fontsize=14, fontweight='bold', color=POS, ha='center')
    fig.text(0.50, 0.135, '                          課題・リスク', fontsize=14,
             fontweight='bold', color=NEG, ha='center')
    return fig

# ════════════════════════════════════════════════════════════════
# 5. 現金900万 活用プラン
# ════════════════════════════════════════════════════════════════
def s5_cash():
    allocs = [
        (0.30, 2_700_000, POS,    '個人向け国債\n（変動10年型）',
         ['日銀利上げで利率が連動上昇（現在0.5%超）',
          '元本保証・1万円から購入可能',
          '1年後から換金可能（中途解約可）',
          'まず安全性最優先の270万円を移行']),
        (0.30, 2_700_000, BLUE1,  'NISA成長投資枠\n一括・積立追加',
         ['年間240万円枠を最大活用',
          'eMAXIS Slim オールカントリーを追加',
          '一括or12ヶ月分割（150万+毎月12.5万）',
          '長期での税メリット最大化']),
        (0.20, 1_800_000, AMBER,  '国内高配当株\n打診買い',
         ['日銀利上げ恩恵株（三菱UFJ・東京海上）追加',
          '配当利回り3〜4%以上が目標',
          'NISA成長枠で購入し非課税配当を享受',
          '円高でも内需株は為替影響が小さい']),
        (0.20, 1_800_000, '#909090','緊急予備金\n（MRF/普通預金）',
         ['生活費6ヶ月分+投資機会用待機資金',
          '市場急落時の「買い場」対応資金',
          '日銀利上げで普通預金金利も上昇中',
          '流動性最優先。すぐ動かせる状態を保持']),
    ]

    fig = new_page(
        label='現金900万円 活用プラン',
        title='現金900万円 活用プラン',
        insight='基本方針：安全資産 → インカム → 成長 の順に段階的に運用へ移行'
    )
    gs = gs_body(fig, 2, 2, hspace=0.35, wspace=0.28, top=0.810, bottom=0.105)

    for i,(pct, amt, clr, title, pts) in enumerate(allocs):
        ax = fig.add_subplot(gs[i//2, i%2])
        ax.set_facecolor(ALTBG); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
        ax.add_patch(Rectangle((0,0.80),1,0.20, color=clr, transform=ax.transAxes))
        ax.text(0.5, 0.960, f'{pct*100:.0f}%  |  {amt/1e4:.0f}万円',
                ha='center', va='center', fontsize=10, fontweight='bold',
                color=WHITE, transform=ax.transAxes)
        ax.text(0.5, 0.852, title.replace('\n', '  '),
                ha='center', va='center', fontsize=8.5, fontweight='bold',
                color=WHITE, transform=ax.transAxes)
        step = 0.65/len(pts)
        for j,pt in enumerate(pts):
            ax.text(0.04, 0.762-j*step, f'• {pt}', fontsize=8.5,
                    color=TEXT2, transform=ax.transAxes)
    return fig

# ════════════════════════════════════════════════════════════════
# 6. プランA — 守り重視
# ════════════════════════════════════════════════════════════════
def s6_plan_a():
    fig = new_page(
        label='プランA',
        title='プランA：守り重視・利益確定型',
        insight='大幅含み益銘柄を一部利益確定。現金900万円を安全資産・NISA積立に振り向けVTI集中を解消'
    )
    ax = fig.add_axes([0.04, 0.105, 0.92, 0.710])
    ax.set_facecolor(BG); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')

    actions = [
        ('SELL', NEG,    '三井物産（8031）',         '200株 ／ +143万確定。+239%達成済み、高値圏での部分利益確定'),
        ('SELL', NEG,    '楽天VTI → 一部解約',       '200万円分。SBI VTIと合算で集中リスク解消。+152%の利益確定'),
        ('SELL', NEG,    'VTI（SBI特定）',            '80株。円高前にドルを円転。残100株は継続保有'),
        ('SELL', NEG,    'SKYT（旧NISA）',            '200株。+578%の旧NISA株。一部確定で利益を守る'),
        ('BUY',  POS,    '個人向け国債（変動10年）',  '現金270万円。日銀利上げで利回り上昇中。元本保証'),
        ('ADD',  BLUE1,  'NISA積立 増額',             '現金から月10万。eMAXIS Slim 積立継続・一括追加'),
        ('HOLD', TEXT2,  'その他全ポジション',         '現状維持。含み益のある銘柄はそのまま継続保有'),
    ]
    for i, (op, clr, name, detail) in enumerate(actions):
        action_row(ax, op, clr, name, detail, y=0.870 - i*0.118)

    # リバランス後配分バー
    ax2 = fig.add_axes([0.04, 0.105, 0.92, 0.040])
    ax2.set_facecolor(FOOTER); ax2.axis('off'); ax2.set_xlim(0,100); ax2.set_ylim(0,1)
    segs = [('日本株 23%',23,BLUE1),('米国株 29%',29,AMBER),('投信 20%',20,POS),
            ('国債・安全 17%',17,PURPLE),('現金 11%',11,'#909090')]
    x=0
    for lbl,w,clr in segs:
        ax2.barh(0.5, w, left=x, height=0.9, color=clr, edgecolor=BG, lw=0.5)
        ax2.text(x+w/2, 0.5, lbl, ha='center', va='center',
                 fontsize=8, color=WHITE, fontweight='bold')
        x += w
    return fig

# ════════════════════════════════════════════════════════════════
# 7. プランB — 積立継続
# ════════════════════════════════════════════════════════════════
def s7_plan_b():
    years = np.arange(0,11)
    base  = GRAND_TOTAL; monthly = 13*10000
    grow6 = [base*(1.06)**y + monthly*12*((1.06**y-1)/0.06) for y in years]
    grow4 = [base*(1.04)**y + monthly*12*((1.04**y-1)/0.04) for y in years]
    flat  = [base + monthly*12*y for y in years]

    fig = new_page(
        label='プランB',
        title='プランB：積立継続・現状維持型',
        insight='ポジションほぼ維持。現金900万円でNISA積立を強化し複利効果を最大化'
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    # 左: シミュレーション
    ax1 = fig.add_subplot(gs[0,0])
    ax1.fill_between(years, [v/1e8 for v in grow4], [v/1e8 for v in grow6],
                     alpha=0.15, color=TEAL)
    ax1.plot(years, [v/1e8 for v in flat],  'o--', color=TEXT2, lw=1.5, ms=4, label='積立のみ(0%)')
    ax1.plot(years, [v/1e8 for v in grow4], 'o-',  color=BLUE2, lw=2,   ms=5, label='年率4%')
    ax1.plot(years, [v/1e8 for v in grow6], 'o-',  color=TEAL,  lw=2.5, ms=6, label='年率6%')
    ax1.set_xticks(years); ax1.set_xticklabels([f'{y}年後' for y in years], fontsize=8)
    ax1.set_ylabel('総資産（億円）', fontsize=9, color=TEXT2)
    ax1.legend(fontsize=9.5, framealpha=0.9, edgecolor=BORDER, fancybox=False)
    for arr,lbl in [(grow6,f'{grow6[-1]/1e8:.1f}億\n(年率6%)'),(grow4,f'{grow4[-1]/1e8:.1f}億\n(年率4%)')]:
        ax1.text(10.1, arr[-1]/1e8, lbl, fontsize=8.5, fontweight='bold', va='center',
                 color=TEAL if arr is grow6 else BLUE2)
    cstyle(ax1, f'月13万積立 資産推移シミュレーション\n（現在{GRAND_TOTAL/1e8:.2f}億円スタート）')

    # 右: アクション一覧
    ax2 = fig.add_subplot(gs[0,1])
    ax2.set_facecolor(BG); ax2.set_xlim(0,1); ax2.set_ylim(0,1); ax2.axis('off')
    ax2.set_title('実施アクション', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')
    b_acts = [
        ('HOLD', TEXT2, '全ポジション継続保有',
         '大幅含み益。長期保有が基本。日々の価格変動に惑わされない'),
        ('ADD',  BLUE1, 'eMAXIS Slim（SBI NISA成長枠）',
         '現金270万→一括投資 + 月10万積立。年240万枠フル活用'),
        ('ADD',  RAKUTEN,'楽天VTI 継続積立',
         '楽天口座で毎月積立を継続（月3〜5万）。楽天ポイント投資も活用'),
        ('DRIP', POS,   '配当金・分配金の再投資',
         'NTT・KDDI・オリックス・三菱商事等の配当をeMAXIS Slimへ'),
        ('HOLD', PURPLE,'米国債4本 満期まで保有',
         '金利収入（USD）を積み上げ。2027年満期後は円建て国債へ移行検討'),
        ('WAIT', AMBER, '残り現金（約450万）は待機資金',
         '相場急落時（日経-10%以上）の買い増しチャンスに備えて保持'),
    ]
    for i,(op,clr,name,detail) in enumerate(b_acts):
        action_row(ax2, op, clr, name, detail, y=0.870-i*0.140, h=0.115)
    return fig

# ════════════════════════════════════════════════════════════════
# 8. プランC — 攻め型（根拠付き推奨銘柄）
# ════════════════════════════════════════════════════════════════
def s8_plan_c():
    # 銘柄: 保有中のSPCX追加 + データ根拠のある候補
    # 根拠はトレーニングデータ（〜2025年8月）に基づく。投資判断は自己責任で。
    cands = [
        # (ティッカー, 銘柄名, 投資額, 根拠データ, ユーザー保有?)
        ('SPCX',  'スペースX',          '50万追加',
         '楽天既保有+37.9%。Starlink衛星通信でほぼ独占的地位',
         True,  TEAL),
        ('NVDA',  'エヌビディア',        '200万',
         'FY25Q1売上+122%。AIデータセンター独占シェア。PER約40倍',
         False, PURPLE),
        ('AMAT',  'アプライドマテリアルズ','100万',
         'AI増産設備投資の直接受益株。PER18〜20倍と割安',
         False, BLUE1),
        ('RKLB',  'ロケットラボ',        '50万',
         '小型ロケット成功率95%超。売上成長+50%。高リスク',
         False, AMBER),
        ('6857',  'アドバンテスト',      '100万',
         'AIチップテスト機器で世界首位。2025年3月期売上+82%',
         False, POS),
        ('6920',  'レーザーテック',      '100万',
         'EUV検査装置の世界唯一メーカー。2024年6月期売上+37%',
         False, '#C08000'),
    ]

    fig = new_page(
        label='プランC',
        title='プランC：攻め型・成長株追加型',
        insight='現含み益+2,491万円がリスク緩衝材。現金600万円をAI・宇宙・半導体テーマへ分散投入'
    )
    gs = gs_body(fig, 1, 2, wspace=0.35)

    # 左: 候補テーブル
    ax1 = fig.add_subplot(gs[0,0])
    ax1.set_facecolor(BG); ax1.set_xlim(0,1); ax1.set_ylim(0,1); ax1.axis('off')
    ax1.set_title('追加投資候補（根拠付き）', fontsize=11, fontweight='bold',
                   color=TEXT, pad=9, loc='left')
    hdrs = ['銘柄', '投資額', '根拠・データ', '既保有']
    rows = [(c[0]+'\n'+c[1], c[2], c[3], '●' if c[4] else '') for c in cands]
    cw   = [0.13, 0.09, 0.68, 0.07]
    t = mtable(ax1, hdrs, rows, col_w=cw, fs=7.5, rs=1.75)
    for (r,c), cell in t.get_celld().items():
        if r > 0 and c == 3:
            cell.get_text().set_color(TEAL); cell.get_text().set_fontweight('bold')

    # 右: 配分パイ + リスク注意
    ax2 = fig.add_subplot(gs[0,1])
    ax2.set_facecolor(BG)
    names2 = [c[0] for c in cands]
    amts2  = [50, 200, 100, 50, 100, 100]
    clrs2  = [c[5] for c in cands]
    wedges, texts, autos = ax2.pie(
        amts2, labels=names2, colors=clrs2,
        autopct='%1.0f%%', startangle=90,
        textprops={'fontsize':10}, wedgeprops={'linewidth':2,'edgecolor':BG},
        explode=[0.03]*len(amts2))
    for at in autos: at.set_fontsize(9); at.set_fontweight('bold')
    ax2.set_title('成長テーマ配分（計600万円）', fontsize=11, fontweight='bold',
                   color=TEXT, pad=10, loc='left')

    # 注意書き
    note = fig.add_axes([0.535, 0.105, 0.435, 0.090])
    note.set_facecolor(ALTBG); note.axis('off'); note.set_xlim(0,1); note.set_ylim(0,1)
    note.add_patch(Rectangle((0,0),1,1, facecolor=ALTBG, edgecolor=NEG, lw=1.5,
                               transform=note.transAxes))
    risks = ['1銘柄の投資額は総資産の3〜5%以内（200〜300万円）を目安に',
             '損切りライン: 取得価格から−20〜30%で撤退',
             '残り300万は相場急落時の買い増し原資として待機',
             '※根拠データは〜2025年8月時点。最新情報を必ず確認']
    note.text(0.03, 0.88, 'リスク管理の原則', fontsize=9, fontweight='bold', color=NEG)
    for i,r in enumerate(risks):
        note.text(0.03, 0.70-i*0.18, f'• {r}', fontsize=7.8, color=TEXT2)
    return fig

# ════════════════════════════════════════════════════════════════
# 9. プランD — 円高対応
# ════════════════════════════════════════════════════════════════
def s9_plan_d():
    fx       = [159, 155, 152, 150, 146, 140]
    us_total = 27840364   # 米国株+債券+楽天SPCX
    diffs    = [(us_total*r/159 - us_total)/1e4 for r in fx]

    fig = new_page(
        label='プランD',
        title='プランD：円高対応・国内回帰型',
        insight='戦略の核心：米国資産2,874万円の為替リスクを段階的にヘッジ。現金900万円は全て円建て安全資産へ'
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    # 左: 為替感応グラフ
    ax1 = fig.add_subplot(gs[0,0])
    clrs2 = [POS if d>=0 else NEG for d in diffs]
    bars  = ax1.bar(range(len(fx)), diffs, color=clrs2, edgecolor=BG, width=0.65, zorder=3)
    ax1.set_xticks(range(len(fx))); ax1.set_xticklabels([f'{r}円' for r in fx], fontsize=10)
    ax1.set_ylabel('円換算 増減（万円）', fontsize=9, color=TEXT2)
    ax1.axhline(0, color=BORDER, lw=1)
    for bar,d in zip(bars,diffs):
        ax1.text(bar.get_x()+bar.get_width()/2,
                 bar.get_height()+(4 if d>=0 else -12),
                 f'{d:+.0f}万', ha='center', fontsize=9, fontweight='bold',
                 color=(POS if d>=0 else NEG))
    ax1.axvline(2.5, color=TEXT2, lw=1.2, ls='--', alpha=0.6)
    ax1.text(2.6, min(diffs)*0.5, '年末予想\n152.5円付近', fontsize=8.5, color=TEXT2)
    cstyle(ax1, '為替変動による米国資産（2,874万円）\n円換算損益シミュレーション')

    # 右: アクション一覧
    ax2 = fig.add_subplot(gs[0,1])
    ax2.set_facecolor(BG); ax2.set_xlim(0,1); ax2.set_ylim(0,1); ax2.axis('off')
    ax2.set_title('実施アクション', fontsize=11, fontweight='bold', color=TEXT, pad=9, loc='left')
    d_acts = [
        ('SELL', NEG,    'VTI（SBI特定）段階売却',
         '円高が進むたびに20〜30株ずつ。159→155→150円で3段階'),
        ('SELL', NEG,    '楽天VTI 一部解約（300万円）',
         '+152%の大幅益を一部確定。VTI系集中の解消にも有効'),
        ('SELL', NEG,    'AMBQ（SBI特定）全売却',
         '取得比+178%。円高・ドル安前に全売却し利益確定'),
        ('BUY',  AMBER,  '国内金融株（三菱UFJ等）追加',
         '日銀利上げで銀行・保険は追い風。円高でも内需株は影響軽微'),
        ('BUY',  POS,    '個人向け国債（変動10年）全額',
         '現金900万円を全額投入。日銀利上げ継続で利率が毎年上昇。元本保証'),
    ]
    for i,(op,clr,name,detail) in enumerate(d_acts):
        action_row(ax2, op, clr, name, detail, y=0.860-i*0.160, h=0.130)
    return fig

# ════════════════════════════════════════════════════════════════
# 10. 5プラン比較マトリックス
# ════════════════════════════════════════════════════════════════
def s10_comparison():
    plan_data = {
        'A:守り重視':  ([3,5,4,3,4], POS),
        'B:積立継続':  ([4,4,3,5,4], BLUE1),
        'C:攻め型':    ([5,2,2,4,5], PURPLE),
        'D:円高対応':  ([3,4,5,3,5], AMBER),
        '現金活用':    ([3,5,5,4,5], TEAL),
    }
    cats = ['リターン\n期待値','リスク\n抑制','円高\n耐性','NISA\n活用','現金\n活用度']
    N = len(cats); angles = [n/N*2*np.pi for n in range(N)] + [0]

    fig = new_page(
        label='5プラン 比較マトリックス',
        title='5プラン 比較マトリックス',
        insight='リスク許容度・投資目標・市場観に応じて選択（複数プランの組み合わせも推奨）'
    )
    gs = gs_body(fig, 1, 2, wspace=0.35)

    # 左: レーダー
    ax1 = fig.add_subplot(gs[0,0], polar=True)
    ax1.set_facecolor(BG)
    for lv in [1,2,3,4,5]:
        xs = [lv/5*np.cos(a) for a in angles[:-1]]+[lv/5*np.cos(angles[0])]
        ys = [lv/5*np.sin(a) for a in angles[:-1]]+[lv/5*np.sin(angles[0])]
        ax1.plot(angles, [lv/5]*(N+1), color=BORDER, lw=0.5, alpha=0.5)
    for lbl,(scores,clr) in plan_data.items():
        vs = [s/5 for s in scores] + [scores[0]/5]
        ax1.plot(angles, vs, color=clr, lw=2, label=lbl)
        ax1.fill(angles, vs, color=clr, alpha=0.07)
    ax1.set_thetagrids(np.degrees(angles[:-1]), cats, fontsize=9)
    ax1.set_ylim(0,1); ax1.set_yticks([0.2,0.4,0.6,0.8,1.0])
    ax1.set_yticklabels(['1','2','3','4','5'], fontsize=7, color=TEXT2)
    ax1.grid(color=BORDER, lw=0.6); ax1.spines['polar'].set_color(BORDER)
    ax1.legend(fontsize=8.5, loc='lower left', bbox_to_anchor=(-0.25,-0.18),
               framealpha=0.9, edgecolor=BORDER, fancybox=False)
    ax1.set_title('プラン別 評価レーダー', fontsize=11, fontweight='bold',
                   color=TEXT, pad=28, loc='left')

    # 右: 比較テーブル
    ax2 = fig.add_subplot(gs[0,1])
    rows = [
        ('想定期間',    '〜1年',      '5〜10年',  '3〜5年',  '1〜2年',  '即時〜1年'),
        ('現金の使い道','国債+NISA',  'NISA増額', '成長株追加','全額国債','4分割'),
        ('期待リターン','★★☆☆☆',  '★★★☆☆','★★★★★','★★☆☆☆','★★★☆☆'),
        ('リスク水準',  '低',         '中',       '高',      '低〜中',  '低'),
        ('円高耐性',    '中〜高',     '中',       '低',      '高',      '高'),
        ('VTI集中解消', '○',          '△',        '△',       '◎',      '○'),
        ('向いている人','利確優先',   '長期積立', '高リターン','円高懸念','バランス'),
    ]
    hdrs = ['', 'A:守り', 'B:積立', 'C:攻め', 'D:円高', '現金活用']
    cw   = [0.22,0.14,0.14,0.14,0.14,0.16]
    t = mtable(ax2, hdrs, rows, col_w=cw, fs=8.0, rs=1.50)
    ax2.set_title('プラン別 特性比較', fontsize=11, fontweight='bold',
                   color=TEXT, pad=9, loc='left')

    # 推奨コンボ
    combo = fig.add_axes([0.535, 0.105, 0.435, 0.040])
    combo.set_facecolor(TEAL); combo.axis('off'); combo.set_xlim(0,1); combo.set_ylim(0,1)
    combo.text(0.5, 0.5,
               '推奨組み合わせ例：「プランB（基本）＋プランA（VTI一部利確）」  or  「プランB（基本）＋現金活用プラン」',
               ha='center', va='center', fontsize=9, color=WHITE, fontweight='bold')
    return fig

# ════════════════════════════════════════════════════════════════
# 11. アクションスケジュール
# ════════════════════════════════════════════════════════════════
def s11_timeline():
    months = ['6月','7月','8月','9月','10月','11月','12月','1月','2月','3月','4月','5月']
    ev_up = [
        (0,  '日銀1.0%\n利上げ済',   NEG,   0.90),
        (2,  '米国\n決算期',          AMBER, 0.83),
        (5,  '米中間\n選挙',          PURPLE,0.90),
        (6,  '日銀追加\n利上げ予想',  NEG,   0.83),
        (10, 'NISA枠\n残高確認',      BLUE1, 0.90),
        (11, '国債MF164\n満期（来年9月）',POS,0.83),
    ]
    ac_dn = [
        (0,  POS,   '現金→\n国債270万'),
        (0,  BLUE1, 'NISA積立\n増額開始'),
        (1,  PURPLE,'成長株\n打診買い'),
        (2,  AMBER, '高配当株\n追加検討'),
        (3,  NEG,   '円高進行なら\nVTI段階売却'),
        (5,  RAKUTEN,'楽天VTI\n一部解約検討'),
        (6,  AMBER, '金融株追加\n（利上げ恩恵）'),
        (8,  NEG,   '三井物産\n利益確定検討'),
        (10, BLUE1, 'NISA枠\n使い切り'),
        (11, POS,   '来年国債\n再投資先検討'),
    ]

    fig = new_page(
        label='アクションスケジュール',
        title='2026年6月〜2027年5月 推奨アクションスケジュール',
        insight='市場イベントと連動した投資行動タイムライン'
    )
    ax = fig.add_axes([0.04, 0.10, 0.92, 0.70])
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(-0.7, 11.7); ax.set_ylim(0, 1)
    n = len(months)
    xs = [i for i in range(n)]

    # タイムライン軸
    ax.axhline(0.50, color=TEXT, lw=2.5, xmin=0.02, xmax=0.98)
    for i,(x,m) in enumerate(zip(xs, months)):
        ax.plot(x, 0.50, 'o', ms=8, color=TEAL, zorder=5)
        ax.text(x, 0.43, m, ha='center', fontsize=8.5, color=TEXT2)

    # 上部イベント
    for idx,lbl,clr,y in ev_up:
        x = xs[idx]
        ax.annotate('', xy=(x,0.525), xytext=(x, y-0.065),
                    arrowprops=dict(arrowstyle='->', color=clr, lw=1.5))
        ax.add_patch(FancyBboxPatch((x-0.48, y-0.065), 0.96, 0.075,
            boxstyle='round,pad=0.02', lw=1.2, edgecolor=clr, facecolor=WHITE))
        ax.text(x, y-0.028, lbl, ha='center', va='center',
                fontsize=7.5, color=clr, fontweight='bold')

    # 下部アクション
    for i, (idx,clr,lbl) in enumerate(ac_dn):
        x = xs[idx]
        yy = 0.34 if i%2==0 else 0.18
        ax.annotate('', xy=(x,0.475), xytext=(x, yy+0.075),
                    arrowprops=dict(arrowstyle='->', color=clr, lw=1.5))
        ax.add_patch(FancyBboxPatch((x-0.48, yy), 0.96, 0.075,
            boxstyle='round,pad=0.02', lw=1.2, edgecolor=clr, facecolor=WHITE))
        ax.text(x, yy+0.037, lbl, ha='center', va='center',
                fontsize=7.5, color=clr, fontweight='bold')

    # 免責
    disc = fig.add_axes([0.04, 0.078, 0.92, 0.025])
    disc.set_facecolor(ALTBG); disc.axis('off'); disc.set_xlim(0,1); disc.set_ylim(0,1)
    disc.text(0.5, 0.5,
              '免責事項：本資料は2026年6月21日時点のデータに基づく情報提供を目的としたものであり、特定の投資を推奨するものではありません。投資判断は必ずご自身の責任においてご判断ください。',
              ha='center', va='center', fontsize=7.5, color=TEXT2)
    return fig

# ── PDF出力 ─────────────────────────────────────────────────────
OUT = "/Users/takahiroazuma/Desktop/kabu/claude/output/investment_plan_v4.pdf"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

slides = [s1_cover, s2_total_summary, s3_rakuten, s4_swot, s5_cash,
          s6_plan_a, s7_plan_b, s8_plan_c, s9_plan_d, s10_comparison, s11_timeline]

A4W = int(297*150/25.4); A4H = int(210*150/25.4)
imgs = []
for i, fn in enumerate(slides):
    print(f"  {i+1}/{len(slides)}: {fn.__name__}")
    fig = fn()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    imgs.append(Image.open(buf).convert('RGB').resize((A4W, A4H), Image.LANCZOS))
    plt.close(fig)

imgs[0].save(OUT, save_all=True, append_images=imgs[1:], resolution=150)
print(f"\n✅  {OUT}  ({os.path.getsize(OUT)//1024} KB)")
