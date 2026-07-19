#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配当金 分析レポート v4 — design01.pdf スタイル
  ・温かみのあるオフホワイト背景
  ・ヘッダーバーなし (タイトルはテキストのみ)
  ・グラフは下線のみ / 縦グリッドなし
  ・テーブルは水平線のみ
  ・黒フッター + 右端ページ番号
出力: output/dividend_report_v4.pdf
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
import numpy as np, pandas as pd, re, io, os, csv, warnings
from PIL import Image
warnings.filterwarnings('ignore')

import matplotlib.font_manager as fm
_JP = next((f.name for f in fm.fontManager.ttflist
            if f.name in ['Hiragino Sans','Hiragino Kaku Gothic ProN',
                          'Yu Gothic','Noto Sans CJK JP']), None)
if _JP: plt.rcParams['font.family'] = _JP
plt.rcParams['axes.unicode_minus'] = False

# ── デザイントークン (design01.pdf 準拠) ──────────────────────
BG     = '#EDEAE6'   # 温かみのあるオフホワイト
TEXT   = '#1A1A1A'   # 本文テキスト (ほぼ黒)
TEXT2  = '#6B6560'   # 副テキスト
TEAL   = '#00B4CC'   # メインアクセント (ティール)
BLUE1  = '#5BAED0'   # 日本株 (落ち着いた青)
BLUE2  = '#8EC8E8'   # 薄い青 (過去期間)
AMBER  = '#D4820C'   # 米国株 (アンバー)
PURPLE = '#8870CC'   # 米国債 (パープル)
POS    = '#2D8A50'   # 上昇
NEG    = '#C03030'   # 下降
FOOTER = '#1C1C1C'   # フッター背景
WHITE  = '#FFFFFF'
HDRBG  = '#D4D0CC'   # テーブルヘッダー行背景
ALTBG  = '#F5F2EE'   # テーブル交互行背景

CAT_C = {'日本株': BLUE1, '米国株・ETF': AMBER, '米国債利息': PURPLE}

# ── CSV 読み込み ─────────────────────────────────────────────
DATA_DIR = "/Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri/data"
# 2021/8/1〜2026/7/11 の全履歴（単一ファイル）
CSV_HIST = f"{DATA_DIR}/DISTRIBUTION_20260711180905.csv"

def _read_csv(path, year_filter=None):
    recs = []
    with open(path, encoding='cp932', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: row = list(csv.reader([line]))[0]
            except: continue
            if len(row) < 6: continue
            if not re.match(r'^20\d\d/\d{1,2}/\d{1,2}$', row[0]): continue
            try:
                yr = int(row[0][:4])
                if year_filter and yr not in year_filter: continue
                recs.append({'date': row[0], 'year': yr,
                             'month': int(row[0].split('/')[1]),
                             'category': row[2], 'name_raw': row[3],
                             'amount': float(row[5].replace(',','').strip())})
            except: continue
    return recs

records = _read_csv(CSV_HIST)

NAME_MAP = [
    ('ＮＴＴ','NTT'),('日本電信電話','NTT'),('ＫＤＤＩ','KDDI'),
    ('三井物産','三井物産'),('蔵王産業','蔵王産業'),('ジャックス','ジャックス'),
    ('オリックス','オリックス'),('三菱ＵＦＪフィナンシャル','三菱UFJ'),
    ('ジェイエイシーリクルートメント','JAC採用'),('ＣＤＳ','CDS'),
    ('武田薬品工業','武田薬品'),('三菱商事','三菱商事'),('伊藤忠商事','伊藤忠'),
    ('バルカー','バルカー'),('三井住友フィナンシャル','三井住友FG'),
    ('東京海上ホールディングス','東京海上'),
    ('第一生命ホールディングス','第一生命'),('第一ライフグループ','第一生命'),
    ('沖縄セルラー電話','沖縄セルラー'),('三菱ＨＣキャピタル','三菱HC'),
    ('アサンテ','アサンテ'),('アビスト','アビスト'),
    ('イー・ギャランティ','Eギャランティ'),('信越化学工業','信越化学'),
    ('九州旅客鉄道','JR九州'),('ソフトバンクグループ','SBG'),('中国電力','中国電力'),
    ('バンガード トータルストックマーケット','VTI'),('米国高配当株 ETF','HDV'),
    ('S&P500高配当株式ETF','SPYD'),('S&P 500高配当株式ETF','SPYD'),
    ('メタ プラットフォームズ','META'),
    ('4.125','米国債4.125%'),('4.750','米国債4.750%'),
    ('4.250','米国債4.250%'),('4.000','米国債4.000%'),
]
def normalize(raw):
    for k, v in NAME_MAP:
        if k in raw: return v
    return re.sub(r'\s+\d{4}$', '', raw).strip()

for r in records:
    r['name'] = normalize(r['name_raw'])
    c = r['category']
    r['cat3'] = ('日本株' if c == '国内株式(現物)' else
                 '米国株・ETF' if c == '米国株式' else '米国債利息')

df = pd.DataFrame(records)
YEARS = sorted(df['year'].unique())
print(f"読込: {len(df)}件  {YEARS[0]}〜{YEARS[-1]}")

# ── ヘルパー ──────────────────────────────────────────────────
def ylbl(y, short=False):
    if y == 2021: return f"{y}\n(9月〜)" if not short else f"{y}※"
    if y == 2026: return f"{y}\n(〜7/11)" if not short else f"{y}※"
    return str(y)

man = lambda v: f"{v/1e4:.1f}万"

# ─────────────────────────────────────────────────────────────
# ページ共通: 白紙 + タイトルテキスト + 黒フッター
# ─────────────────────────────────────────────────────────────
_PAGE_NUM = [0]

def new_page(label='', title='', insight=''):
    """
    背景: BG  /  ヘッダーバーなし  /  下部黒フッター
    GridSpec コンテンツ領域: top=0.80, bottom=0.10
    """
    _PAGE_NUM[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)

    # ── タイトルテキスト (ヘッダーバーなし) ──
    if label:
        fig.text(0.04, 0.935, label, fontsize=9.5, color=TEXT2,
                 fontweight='normal', va='center')
    if title:
        fig.text(0.04, 0.885, title, fontsize=16, color=TEXT,
                 fontweight='bold', va='center')
    if insight:
        fig.text(0.04, 0.840, insight, fontsize=10, color=TEXT2,
                 va='center')

    # ── 仕切り線 ──
    hline = fig.add_axes([0.04, 0.822, 0.92, 0.002])
    hline.set_facecolor('#C8C4BE'); hline.axis('off')

    # ── 黒フッター ──
    foot = fig.add_axes([0, 0, 1, 0.075])
    foot.set_facecolor(FOOTER); foot.axis('off')
    foot.set_xlim(0, 1); foot.set_ylim(0, 1)
    foot.text(0.04, 0.45, '個人投資ポートフォリオ  配当金分析  2026年7月11日',
              color='#909090', fontsize=8, va='center')
    foot.text(0.96, 0.45, str(_PAGE_NUM[0]), color='#D0D0D0',
              fontsize=11, fontweight='bold', ha='right', va='center')

    return fig

def gs_content(fig, nrows=1, ncols=1, hspace=0.45, wspace=0.30,
               top=0.810, bottom=0.105):
    """コンテンツ領域の GridSpec を返す"""
    return GridSpec(nrows, ncols, figure=fig,
                    left=0.04, right=0.97,
                    bottom=bottom, top=top,
                    hspace=hspace, wspace=wspace)

def chart_style(ax, title='', ylabel='', xlabel=''):
    """design01 風: 下線のみ / 横グリッドのみ / 背景 BG"""
    ax.set_facecolor(BG)
    ax.yaxis.grid(True, color='#C8C4BE', lw=0.6, zorder=0)
    ax.xaxis.grid(False)
    ax.spines['bottom'].set_color('#C0BCB8')
    ax.spines['bottom'].set_linewidth(0.8)
    ax.spines[['top','right','left']].set_visible(False)
    ax.tick_params(axis='both', length=0, labelsize=9.5, colors=TEXT2)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0f}万'))
    if title:
        ax.set_title(title, fontsize=11, fontweight='bold',
                     color=TEXT, pad=10, loc='left')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=TEXT2)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=TEXT2)

def bar_labels(ax, bars, fmt='{:.1f}万', offset_frac=0.04):
    """棒グラフの上にラベル"""
    heights = [b.get_height() for b in bars]
    mx = max(heights) if heights else 1
    for b in bars:
        h = b.get_height()
        if h <= 0: continue
        ax.text(b.get_x() + b.get_width()/2,
                h + mx * offset_frac,
                fmt.format(h),
                ha='center', va='bottom',
                fontsize=8.5, fontweight='bold', color=TEXT)

def make_table(ax, headers, rows, col_w=None, fs=9.0, row_scale=1.6):
    """水平線のみ風テーブル (design01 スタイル)"""
    kw = dict(cellText=rows, colLabels=headers, cellLoc='center', loc='center')
    if col_w: kw['colWidths'] = col_w
    t = ax.table(**kw)
    t.auto_set_font_size(False)
    t.set_fontsize(fs)
    t.scale(1, row_scale)
    for (r, c), cell in t.get_celld().items():
        cell.set_linewidth(0.4)
        if r == 0:
            cell.set_facecolor(HDRBG)
            cell.set_edgecolor('#B8B4B0')
            cell.get_text().set_color(TEXT)
            cell.get_text().set_fontweight('bold')
        elif r % 2 == 0:
            cell.set_facecolor(ALTBG)
            cell.set_edgecolor('#D0CCC8')
        else:
            cell.set_facecolor(BG)
            cell.set_edgecolor('#D0CCC8')
    ax.axis('off')
    return t

# ══════════════════════════════════════════════════════════════
# 1. 表紙
# ══════════════════════════════════════════════════════════════
def s1_cover():
    _PAGE_NUM[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)

    # 左: アクセントブロック (ティール) - design01 の左側カラードブロック風
    left = fig.add_axes([0, 0.12, 0.38, 0.78])
    left.set_facecolor(TEAL); left.axis('off')
    left.set_xlim(0,1); left.set_ylim(0,1)

    # 右: テキスト
    fig.text(0.44, 0.78, '配当金収入', fontsize=30, fontweight='bold',
             color=TEXT, va='center')
    fig.text(0.44, 0.68, '分析レポート', fontsize=30, fontweight='bold',
             color=TEXT, va='center')
    fig.text(0.44, 0.58, 'SBI証券  ／  2021年9月〜2026年7月11日',
             fontsize=13, color=TEXT2, va='center')

    total = df['amount'].sum()
    kpis = [
        (f"{total/1e4:.1f}万円",   '累計配当合計（税引後）', TEAL),
        (f"{df[df['cat3']=='日本株']['amount'].sum()/1e4:.1f}万円", '日本株 配当', BLUE1),
        (f"{df[df['cat3']=='米国株・ETF']['amount'].sum()/1e4:.1f}万円", '米国株・ETF', AMBER),
        (f"{df[df['cat3']=='米国債利息']['amount'].sum()/1e4:.1f}万円", '米国債 利息', PURPLE),
    ]
    for i, (val, lbl, clr) in enumerate(kpis):
        ky = 0.44 - i * 0.085
        fig.text(0.44, ky, val, fontsize=16, fontweight='bold',
                 color=clr, va='center')
        fig.text(0.67, ky, lbl, fontsize=10, color=TEXT2, va='center')

    # 区切り線
    div = fig.add_axes([0.44, 0.085, 0.52, 0.002])
    div.set_facecolor('#C8C4BE'); div.axis('off')

    fig.text(0.44, 0.055, f'全 {len(df)} 件収録  ※2021年は9月から、2026年は7月11日まで',
             fontsize=9, color=TEXT2, va='center')

    # フッター
    foot = fig.add_axes([0, 0, 1, 0.075])
    foot.set_facecolor(FOOTER); foot.axis('off')
    foot.set_xlim(0,1); foot.set_ylim(0,1)
    foot.text(0.5, 0.45, '個人投資ポートフォリオ  配当金分析  2026年7月11日',
              ha='center', color='#909090', fontsize=8, va='center')
    foot.text(0.96, 0.45, '1', color='#D0D0D0', fontsize=11,
              fontweight='bold', ha='right', va='center')
    return fig

# ══════════════════════════════════════════════════════════════
# 2. 年別配当推移
# ══════════════════════════════════════════════════════════════
def s2_annual():
    by_yc  = df.groupby(['year','cat3'])['amount'].sum().unstack(fill_value=0)
    for c in ['日本株','米国株・ETF','米国債利息']:
        if c not in by_yc.columns: by_yc[c] = 0
    total_y = df.groupby('year')['amount'].sum()

    fig = new_page(
        label='配当金 年別推移',
        title='年別 配当金 推移と合計',
        insight=f"累計 {df['amount'].sum()/1e4:.1f}万円（税引後）  ／  "
                f"2025年が最高年 {total_y.get(2025,0)/1e4:.1f}万円"
    )
    gs = gs_content(fig, 1, 2, wspace=0.35)

    # ─ 左: 積み上げ棒グラフ ─
    ax1 = fig.add_subplot(gs[0, 0])
    xs = np.arange(len(YEARS)); bot = np.zeros(len(YEARS))
    for cat in ['日本株','米国株・ETF','米国債利息']:
        v = [by_yc.loc[y,cat]/1e4 if y in by_yc.index else 0 for y in YEARS]
        clr = TEAL if cat=='日本株' else CAT_C[cat]
        ax1.bar(xs, v, 0.58, bottom=bot,
                color=CAT_C[cat], edgecolor=BG, lw=0.8, label=cat, zorder=3)
        bot += np.array(v)
    # 合計ラベル
    mx = total_y.max()/1e4
    for i, y in enumerate(YEARS):
        t = total_y.get(y, 0)/1e4
        ax1.text(i, t + mx*0.025, f'{t:.1f}万',
                 ha='center', fontsize=9, fontweight='bold', color=TEXT)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([ylbl(y, short=True) for y in YEARS], fontsize=9.5)
    ax1.legend(fontsize=9, loc='upper left', framealpha=0.9,
               edgecolor='#C8C4BE', fancybox=False)
    chart_style(ax1, '年別カテゴリ別 配当合計', '万円')

    # ─ 右: 年別合計テーブル ─
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(BG); ax2.axis('off')
    ax2.set_title('年別合計（万円）', fontsize=11, fontweight='bold',
                   color=TEXT, pad=10, loc='left')
    hdrs = ['年', '日本株', '米国ETF', '米国債', '合計']
    rows = []
    for y in YEARS:
        jp = by_yc.loc[y,'日本株'] if y in by_yc.index else 0
        us = by_yc.loc[y,'米国株・ETF'] if y in by_yc.index else 0
        bd = by_yc.loc[y,'米国債利息'] if y in by_yc.index else 0
        tag = '※' if y in (2021,2026) else ''
        rows.append([f'{y}{tag}', f'{jp/1e4:.1f}', f'{us/1e4:.1f}',
                     f'{bd/1e4:.1f}', f'{(jp+us+bd)/1e4:.1f}'])
    make_table(ax2, hdrs, rows,
               col_w=[0.24,0.19,0.19,0.19,0.19], fs=9.5, row_scale=1.75)

    return fig

# ══════════════════════════════════════════════════════════════
# 3. 月別パターン
# ══════════════════════════════════════════════════════════════
def s3_monthly():
    MJ = ['1','2','3','4','5','6','7','8','9','10','11','12']
    key_m = [3, 5, 6, 9, 11, 12]

    fig = new_page(
        label='配当金 月別パターン',
        title='月別 配当受取パターン',
        insight='6・12月: 日本株決算  ／  3・6・9・12月: 米国ETF四半期  ／  5・11月: 米国債利息'
    )
    gs = gs_content(fig, 2, 2, hspace=0.55, wspace=0.35)

    xs = np.arange(12)

    # ─ 左上: 全期間月別積み上げ ─
    ax1 = fig.add_subplot(gs[0, 0])
    bot = np.zeros(12)
    for cat in ['日本株','米国株・ETF','米国債利息']:
        v = [df[(df['cat3']==cat)&(df['month']==m+1)]['amount'].sum()/1e4 for m in range(12)]
        ax1.bar(xs, v, 0.68, bottom=bot,
                color=CAT_C[cat], edgecolor=BG, lw=0.7, label=cat, zorder=3)
        bot += np.array(v)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([f'{m}月' for m in range(1,13)], fontsize=8.5)
    ax1.legend(fontsize=8.5, framealpha=0.9, edgecolor='#C8C4BE', fancybox=False)
    chart_style(ax1, '全期間 月別累計配当', '万円')

    # ─ 右上: 2025年月別 ─
    ax2 = fig.add_subplot(gs[0, 1])
    df25 = df[df['year']==2025]; bot2 = np.zeros(12)
    for cat in ['日本株','米国株・ETF','米国債利息']:
        v = [df25[(df25['cat3']==cat)&(df25['month']==m+1)]['amount'].sum()/1e4 for m in range(12)]
        ax2.bar(xs, v, 0.68, bottom=bot2,
                color=CAT_C[cat], edgecolor=BG, lw=0.7, label=cat, zorder=3)
        bot2 += np.array(v)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([f'{m}月' for m in range(1,13)], fontsize=8.5)
    ax2.legend(fontsize=8.5, framealpha=0.9, edgecolor='#C8C4BE', fancybox=False)
    chart_style(ax2, '2025年 月別内訳', '万円')

    # ─ 下段全幅: 主要月テーブル ─
    ax3 = fig.add_subplot(gs[1, :])
    ax3.set_facecolor(BG); ax3.axis('off')
    ax3.set_title('主要入金月 × 年別配当（万円）',
                   fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')
    tot_all = df['amount'].sum()
    hdrs = ['月'] + [str(y) for y in YEARS] + ['合計', '比率']
    rows = []
    for m in key_m:
        mt = df[df['month']==m]['amount'].sum()
        yv = [df[(df['year']==y)&(df['month']==m)]['amount'].sum() for y in YEARS]
        rows.append(
            [f'{m}月'] +
            [f'{v/1e4:.1f}' if v>0 else '—' for v in yv] +
            [f'{mt/1e4:.1f}万', f'{mt/tot_all*100:.1f}%']
        )
    nc = 1 + len(YEARS) + 2
    cw = [0.07] + [0.10]*len(YEARS) + [0.10, 0.08]
    s  = sum(cw); cw = [w/s for w in cw]
    make_table(ax3, hdrs, rows, col_w=cw, fs=9.0, row_scale=1.65)

    return fig

# ══════════════════════════════════════════════════════════════
# 4. 日本株 銘柄別
# ══════════════════════════════════════════════════════════════
def s4_jp():
    jp = df[df['cat3']=='日本株']
    by_ny = jp.groupby(['name','year'])['amount'].sum().unstack(fill_value=0)
    for y in YEARS:
        if y not in by_ny.columns: by_ny[y] = 0
    by_ny = by_ny[sorted(by_ny.columns)]
    tots  = by_ny.sum(axis=1).sort_values(ascending=False)
    top8  = tots.head(8).index.tolist()

    fig = new_page(
        label='日本株 銘柄別分析',
        title='日本株 銘柄別・年別 配当推移',
        insight=f"日本株 累計: {jp['amount'].sum()/1e4:.1f}万円  ／  上位8銘柄を表示"
    )
    gs = gs_content(fig, 2, 2, hspace=0.55, wspace=0.35)

    # ─ 左上: 累計水平棒グラフ ─
    ax1 = fig.add_subplot(gs[0, 0])
    ns = top8[::-1]
    vs = [tots[n]/1e4 for n in ns]
    # 上位3は TEAL、それ以外は BLUE2
    clrs = [TEAL if i >= len(ns)-3 else BLUE2 for i in range(len(ns))]
    bars = ax1.barh(range(len(ns)), vs, color=clrs,
                    edgecolor=BG, height=0.60, lw=0.7, zorder=3)
    ax1.set_yticks(range(len(ns)))
    ax1.set_yticklabels(ns, fontsize=9.5)
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    mv = max(vs) if vs else 1
    for b, v in zip(bars, vs):
        ax1.text(b.get_width() + mv*0.03, b.get_y()+b.get_height()/2,
                 f'{v:.1f}万', va='center', fontsize=8.5,
                 fontweight='bold', color=TEXT)
    ax1.set_xlim(0, mv*1.30)
    ax1.set_facecolor(BG)
    ax1.xaxis.grid(True, color='#C8C4BE', lw=0.6, zorder=0)
    ax1.yaxis.grid(False)
    ax1.spines['bottom'].set_color('#C0BCB8'); ax1.spines['bottom'].set_lw(0.8)
    ax1.spines[['top','right','left']].set_visible(False)
    ax1.tick_params(length=0, labelsize=9.5, colors=TEXT2)
    ax1.set_title('累計ランキング（上位8銘柄）',
                   fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')

    # ─ 右上: 上位5銘柄 年次折れ線 ─
    ax2 = fig.add_subplot(gs[0, 1])
    lclrs = [TEAL, BLUE1, POS, AMBER, PURPLE]
    for name, clr in zip(top8[:5], lclrs):
        yv = [by_ny.loc[name,y]/1e4 if name in by_ny.index else 0 for y in YEARS]
        ax2.plot(YEARS, yv, 'o-', color=clr, lw=2, ms=6, label=name, zorder=3)
        if yv[-1] > 0:
            ax2.annotate(f'{yv[-1]:.1f}万', xy=(YEARS[-1], yv[-1]),
                         xytext=(5,0), textcoords='offset points',
                         fontsize=8.5, color=clr, va='center', fontweight='bold')
    ax2.set_xticks(YEARS)
    ax2.set_xticklabels([str(y) for y in YEARS], fontsize=9, rotation=25, ha='right')
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.1f}万'))
    ax2.legend(fontsize=8.5, framealpha=0.9, edgecolor='#C8C4BE', fancybox=False, ncol=2)
    chart_style(ax2, '上位5銘柄 年次推移', '万円')

    # ─ 下段全幅: テーブル ─
    ax3 = fig.add_subplot(gs[1, :])
    ax3.set_facecolor(BG); ax3.axis('off')
    ax3.set_title('銘柄別 年間配当一覧（万円 / 直近4年）',
                   fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')
    show_y = [y for y in YEARS if y >= 2023]
    hdrs   = ['銘柄', '累計'] + [ylbl(y,short=True) for y in show_y] + ['前年比', '傾向']
    rows   = []
    for n in top8:
        cum = tots[n]
        v24 = by_ny.loc[n,2024] if (n in by_ny.index and 2024 in by_ny.columns) else 0
        v25 = by_ny.loc[n,2025] if (n in by_ny.index and 2025 in by_ny.columns) else 0
        yoy = f'{(v25/v24-1)*100:+.0f}%' if v24 > 0 else '—'
        tr  = '↑' if v25>v24*1.05 else '↓' if v25<v24*0.95 else '→'
        yv  = [f'{by_ny.loc[n,y]/1e4:.1f}' if (n in by_ny.index and y in by_ny.columns)
               else '—' for y in show_y]
        rows.append([n, f'{cum/1e4:.1f}'] + yv + [yoy, tr])
    cw = [0.18, 0.09] + [0.13]*len(show_y) + [0.09, 0.07]
    s  = sum(cw); cw = [w/s for w in cw]
    make_table(ax3, hdrs, rows, col_w=cw, fs=9.0, row_scale=1.58)

    jp25 = jp[jp['year']==2025]['amount'].sum()
    jp24 = jp[jp['year']==2024]['amount'].sum()
    return fig

# ══════════════════════════════════════════════════════════════
# 5. 米国株・ETF・米国債
# ══════════════════════════════════════════════════════════════
def s5_us():
    us_df = df[df['cat3'] != '日本株']
    by_ny = us_df.groupby(['name','year'])['amount'].sum().unstack(fill_value=0)
    for y in YEARS:
        if y not in by_ny.columns: by_ny[y] = 0
    by_ny = by_ny[sorted(by_ny.columns)]
    tots  = by_ny.sum(axis=1).sort_values(ascending=False)

    etfs  = [n for n in ['HDV','VTI','SPYD','META'] if n in by_ny.index]
    bonds = [n for n in by_ny.index if '米国債' in n]
    ec    = [TEAL, BLUE1, POS, AMBER]
    bc    = [PURPLE, '#A080E8', '#C050A0', '#E06030']

    fig = new_page(
        label='米国株・ETF・米国債 銘柄別分析',
        title='米国株・ETF・米国債 銘柄別配当推移',
        insight=f"米国ETF: {df[df['cat3']=='米国株・ETF']['amount'].sum()/1e4:.1f}万円  ／  "
                f"米国債: {df[df['cat3']=='米国債利息']['amount'].sum()/1e4:.1f}万円（税引後）"
    )
    gs = gs_content(fig, 2, 2, hspace=0.55, wspace=0.35)

    # ─ 左上: ETF棒グラフ ─
    ax1 = fig.add_subplot(gs[0, 0])
    ny = len(YEARS); bw = 0.66/max(len(etfs),1)
    for ti,(n,clr) in enumerate(zip(etfs,ec)):
        offs = np.arange(ny) - 0.33 + (ti+0.5)*bw
        vs   = [by_ny.loc[n,y]/1e4 for y in YEARS]
        b = ax1.bar(offs, vs, bw*0.85, color=clr,
                    edgecolor=BG, lw=0.7, label=n, zorder=3)
    ax1.set_xticks(np.arange(ny))
    ax1.set_xticklabels([ylbl(y,short=True) for y in YEARS], fontsize=9, rotation=20, ha='right')
    ax1.legend(fontsize=9, framealpha=0.9, edgecolor='#C8C4BE', fancybox=False)
    chart_style(ax1, '米国ETF・株 年別配当', '万円')

    # ─ 右上: 米国債棒グラフ ─
    ax2 = fig.add_subplot(gs[0, 1])
    bw2 = 0.66/max(len(bonds),1)
    for bi,(n,clr) in enumerate(zip(bonds,bc)):
        offs = np.arange(ny) - 0.33 + (bi+0.5)*bw2
        vs   = [by_ny.loc[n,y]/1e4 for y in YEARS]
        ax2.bar(offs, vs, bw2*0.85, color=clr,
                edgecolor=BG, lw=0.7, label=n, zorder=3)
    ax2.set_xticks(np.arange(ny))
    ax2.set_xticklabels([ylbl(y,short=True) for y in YEARS], fontsize=9, rotation=20, ha='right')
    ax2.legend(fontsize=8.5, framealpha=0.9, edgecolor='#C8C4BE', fancybox=False)
    chart_style(ax2, '米国債 年別利息収入', '万円')

    # ─ 下段全幅: テーブル ─
    ax3 = fig.add_subplot(gs[1, :])
    ax3.set_facecolor(BG); ax3.axis('off')
    ax3.set_title('銘柄別 年間配当一覧（万円 / 直近4年）',
                   fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')
    show_y = [y for y in YEARS if y >= 2023]
    hdrs   = ['銘柄', '区分', '累計'] + [ylbl(y,short=True) for y in show_y] + ['前年比']
    rows   = []
    for n in tots.index:
        cat_m = us_df[us_df['name']==n]['cat3'].mode()
        cs    = 'ETF' if (len(cat_m)>0 and cat_m[0]=='米国株・ETF') else '米国債'
        cum   = tots[n]
        v24   = by_ny.loc[n,2024] if 2024 in by_ny.columns else 0
        v25   = by_ny.loc[n,2025] if 2025 in by_ny.columns else 0
        yoy   = f'{(v25/v24-1)*100:+.0f}%' if v24>0 else '—'
        yv    = [f'{by_ny.loc[n,y]/1e4:.1f}' if y in by_ny.columns else '—' for y in show_y]
        rows.append([n, cs, f'{cum/1e4:.1f}'] + yv + [yoy])
    cw = [0.17, 0.08, 0.09] + [0.13]*len(show_y) + [0.09]
    s  = sum(cw); cw = [w/s for w in cw]
    make_table(ax3, hdrs, rows, col_w=cw, fs=9.0, row_scale=1.58)

    return fig

# ══════════════════════════════════════════════════════════════
# 6. 累計ランキング
# ══════════════════════════════════════════════════════════════
def s6_ranking():
    by_name = df.groupby('name')['amount'].sum().sort_values(ascending=False)
    by_year = df.groupby('year')['amount'].sum()
    fy      = [y for y in YEARS if y not in (2021,2026)]

    fig = new_page(
        label='全銘柄 累計ランキング',
        title='全銘柄 累計配当ランキング',
        insight=f"全{len(by_name)}銘柄  ／  累計総額: {df['amount'].sum()/1e4:.1f}万円（税引後）"
    )
    gs = gs_content(fig, 2, 2, hspace=0.45, wspace=0.35)

    # ─ 左全体: 水平棒グラフ（上位20） ─
    ax1 = fig.add_subplot(gs[:, 0])  # 全高さ
    ns  = by_name.index[:20].tolist()[::-1]
    vs  = [by_name[n]/1e4 for n in ns]
    def ncat(n):
        m = df[df['name']==n]['cat3'].mode()
        return (BLUE1 if len(m)>0 and m[0]=='日本株' else
                AMBER if len(m)>0 and m[0]=='米国株・ETF' else PURPLE)
    # 最大値の銘柄だけ TEAL
    max_n = by_name.index[0]
    clrs  = [TEAL if n==max_n else ncat(n) for n in ns]
    bars  = ax1.barh(range(len(ns)), vs, color=clrs,
                     edgecolor=BG, height=0.65, lw=0.7, zorder=3)
    ax1.set_yticks(range(len(ns)))
    ax1.set_yticklabels(ns, fontsize=9.5)
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:.0f}万'))
    mv = max(vs)
    for b, v in zip(bars, vs):
        ax1.text(b.get_width()+mv*0.025, b.get_y()+b.get_height()/2,
                 f'{v:.1f}万', va='center', fontsize=9, fontweight='bold', color=TEXT)
    ax1.set_xlim(0, mv*1.30)
    ax1.legend(handles=[mpatches.Patch(color=BLUE1, label='日本株'),
                         mpatches.Patch(color=AMBER, label='米国ETF'),
                         mpatches.Patch(color=PURPLE,label='米国債'),
                         mpatches.Patch(color=TEAL,  label='最高累計')],
               fontsize=9, loc='lower right', framealpha=0.9,
               edgecolor='#C8C4BE', fancybox=False)
    ax1.set_facecolor(BG)
    ax1.xaxis.grid(True, color='#C8C4BE', lw=0.6, zorder=0)
    ax1.yaxis.grid(False)
    ax1.spines['bottom'].set_color('#C0BCB8'); ax1.spines['bottom'].set_lw(0.8)
    ax1.spines[['top','right','left']].set_visible(False)
    ax1.tick_params(length=0, labelsize=9.5, colors=TEXT2)
    ax1.set_title('累計配当ランキング（上位20銘柄）',
                   fontsize=11, fontweight='bold', color=TEXT, pad=10, loc='left')

    # ─ 右上: 通年合計棒グラフ ─
    ax2 = fig.add_subplot(gs[0, 1])
    fv    = [by_year.get(y,0)/1e4 for y in fy]
    mx_v  = max(fv)
    clr2  = [TEAL if v==mx_v else BLUE2 for v in fv]
    bars2 = ax2.bar(range(len(fy)), fv, color=clr2,
                    edgecolor=BG, lw=0.8, width=0.60, zorder=3)
    bar_labels(ax2, bars2)
    ax2.set_xticks(range(len(fy)))
    ax2.set_xticklabels([str(y) for y in fy], fontsize=10.5)
    chart_style(ax2, '通年ベース 年別合計', '万円')

    # ─ 右下: 展望テキスト ─
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor(BG)
    ax3.set_xlim(0,1); ax3.set_ylim(0,1); ax3.axis('off')
    ax3.add_patch(Rectangle((0,0),1,1, facecolor='#F5F2EE',
                              edgecolor='#C8C4BE', lw=0.8,
                              transform=ax3.transAxes))
    y26 = by_year.get(2026,0)
    y25 = by_year.get(2025,0)
    y22 = by_year.get(2022,0)
    ax3.text(0.06, 0.92, '今後の展望', fontsize=11, fontweight='bold',
             color=TEXT, transform=ax3.transAxes)
    pts = [
        (TEAL,  '安定増配トレンド',
         '三井物産・三菱UFJ等が連続増配継続。\n蔵王産業・JAC採用も高水準を維持。'),
        (AMBER, 'HDV NISA追加効果',
         'NISA枠での追加取得により\n非課税配当収入が拡大中。'),
        (PURPLE,'米国債4.250%満期',
         '2025年6月に償還済み。3銘柄体制で\n年間利息約15万円ペースを継続。'),
        (BLUE1, '2026年受取ペース',
         f'7/11時点で{y26/1e4:.1f}万円受取済み。\n年換算 約{y26/(6+11/30)*12/1e4:.0f}万円ペース。'),
    ]
    for i, (clr, title, desc) in enumerate(pts):
        iy = 0.76 - i * 0.20
        ax3.add_patch(Rectangle((0.03,iy), 0.006, 0.14,
                                  color=clr, transform=ax3.transAxes))
        ax3.text(0.07, iy+0.095, title, fontsize=9.5, fontweight='bold',
                 color=clr, transform=ax3.transAxes)
        ax3.text(0.07, iy+0.025, desc, fontsize=8.5, color=TEXT2,
                 transform=ax3.transAxes)

    return fig

# ── PDF 出力 ─────────────────────────────────────────────────
OUT = "/Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri/output/dividend_report_v4.pdf"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

slides = [s1_cover, s2_annual, s3_monthly, s4_jp, s5_us, s6_ranking]
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
