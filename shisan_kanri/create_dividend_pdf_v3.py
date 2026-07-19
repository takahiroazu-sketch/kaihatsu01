#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配当金 分析レポート v3 — GridSpec + ax.table() で重なり根絶
出力: output/dividend_report_v3.pdf
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec
import numpy as np, pandas as pd, re, io, os, csv, warnings
from PIL import Image
warnings.filterwarnings('ignore')

import matplotlib.font_manager as fm
_JP = next((f.name for f in fm.fontManager.ttflist
            if f.name in ['Hiragino Sans','Hiragino Kaku Gothic ProN',
                          'Yu Gothic','Noto Sans CJK JP']), None)
if _JP: plt.rcParams['font.family'] = _JP
plt.rcParams['axes.unicode_minus'] = False

# ── カラー ──────────────────────────────────────────────────────
NAVY   = '#0A2540'
BLUE   = '#1A6FBF'   # 日本株
ORANGE = '#D45D00'   # 米国株
PURPLE = '#6929C4'   # 債券
GOLD   = '#C07800'   # ハイライト
GREEN  = '#15803D'
RED    = '#B91C1C'
GRAY   = '#6B7280'
LIGHT  = '#EEF4FF'   # テーブル交互行
BORDER = '#CBD5E1'
WHITE  = '#FFFFFF'
BG     = '#FFFFFF'
CAT_C  = {'日本株': BLUE, '米国株・ETF': ORANGE, '米国債利息': PURPLE}

# ── CSV ─────────────────────────────────────────────────────────
CSV = "/Users/takahiroazuma/Desktop/kabu/claude/data/DISTRIBUTION_20260627095220.csv"
with open(CSV, encoding='cp932', errors='replace') as f:
    lines = f.readlines()

records = []
for line in lines:
    line = line.strip()
    if not line: continue
    try: row = list(csv.reader([line]))[0]
    except: continue
    if len(row) < 6: continue
    if not re.match(r'^20\d\d/\d{1,2}/\d{1,2}$', row[0]): continue
    try:
        records.append({'date': row[0], 'year': int(row[0][:4]),
                        'month': int(row[0].split('/')[1]),
                        'category': row[2], 'name_raw': row[3],
                        'amount': float(row[5].replace(',','').strip())})
    except: continue

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
    for k,v in NAME_MAP:
        if k in raw: return v
    return re.sub(r'\s+\d{4}$','',raw).strip()

for r in records:
    r['name'] = normalize(r['name_raw'])
    c = r['category']
    r['cat3'] = ('日本株' if c=='国内株式(現物)' else
                 '米国株・ETF' if c=='米国株式' else '米国債利息')

df = pd.DataFrame(records)
YEARS = sorted(df['year'].unique())
print(f"読込: {len(df)}件  {YEARS[0]}〜{YEARS[-1]}")

def ylbl(y):
    if y==2021: return f"{y}\n(9月〜)"
    if y==2026: return f"{y}\n(〜6/26)"
    return str(y)

# ── スライド基本構造 ─────────────────────────────────────────────
# header_ax: [0, 0.912, 1, 0.088]  ← ここにタイトル
# content:    GridSpec(top=0.905, bottom=0.068)
# footer_ax: [0, 0, 1, 0.060]      ← ここに注釈

def make_slide(title, subtitle='', accent=BLUE):
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)
    # header
    h = fig.add_axes([0, 0.912, 1, 0.088])
    h.set_facecolor(NAVY); h.axis('off')
    h.set_xlim(0,1); h.set_ylim(0,1)
    h.add_patch(Rectangle((0,0),1,0.09,color=accent,transform=h.transAxes))
    h.text(0.016, 0.70, title, color=WHITE, fontsize=17, fontweight='bold',
           va='center', transform=h.transAxes)
    if subtitle:
        h.text(0.016, 0.22, subtitle, color='#AECCE8', fontsize=8.5,
               va='center', transform=h.transAxes)
    # footer
    f = fig.add_axes([0, 0, 1, 0.060])
    f.set_facecolor('#F1F5F9'); f.axis('off')
    return fig

def footer_text(fig, text):
    fig.text(0.5, 0.028, text, ha='center', va='center',
             fontsize=9, color=GRAY, transform=fig.transFigure)

def chart_style(ax, title='', ylabel=''):
    ax.set_facecolor('#FAFBFD')
    ax.grid(axis='y', color=BORDER, lw=0.7, alpha=0.9, zorder=0)
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color(BORDER)
    ax.tick_params(colors='#374151', labelsize=9.5)
    if title: ax.set_title(title, fontsize=11, fontweight='bold',
                            color=NAVY, pad=7, loc='left')
    if ylabel: ax.set_ylabel(ylabel, fontsize=9.5, color=GRAY)

def make_table(ax, headers, rows, col_w=None, fs=9, scale=1.55):
    kw = dict(cellText=rows, colLabels=headers, cellLoc='center', loc='center')
    if col_w: kw['colWidths'] = col_w
    t = ax.table(**kw)
    t.auto_set_font_size(False)
    t.set_fontsize(fs)
    t.scale(1, scale)
    for (r,c), cell in t.get_celld().items():
        cell.set_linewidth(0.5)
        cell.set_edgecolor(BORDER)
        if r == 0:
            cell.set_facecolor(NAVY)
            cell.get_text().set_color(WHITE)
            cell.get_text().set_fontweight('bold')
        elif r % 2 == 0:
            cell.set_facecolor(LIGHT)
        else:
            cell.set_facecolor(WHITE)
    ax.axis('off')
    return t

# ══════════════════════════════════════════════════════════════
# 1. 表紙
# ══════════════════════════════════════════════════════════════
def s1_cover():
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(NAVY)

    fig.text(0.5,0.80,'配当金収入 分析レポート',ha='center',color=WHITE,
             fontsize=34,fontweight='bold')
    fig.text(0.5,0.70,'SBI証券   2021年9月 〜 2026年6月26日',ha='center',
             color='#F5A623',fontsize=17,fontweight='bold')
    fig.text(0.5,0.62,f'全 {len(df)} 件収録   ※2021年9月から / 2026年6月26日までの部分データ含む',
             ha='center',color='#7FA8C9',fontsize=10.5)

    # 区切りライン
    fig.add_axes([0.05,0.57,0.90,0.003]).set_facecolor('#F5A623') or None
    la = fig.add_axes([0.05,0.57,0.90,0.003]); la.set_facecolor('#F5A623'); la.axis('off')

    total = df['amount'].sum()
    kpis = [
        ('累計配当合計（税後）',f"{total/1e4:.1f}万円",'',             '#F5A623'),
        ('日本株 配当',          f"{df[df['cat3']=='日本株']['amount'].sum()/1e4:.1f}万円",
         '特定・NISA口座', BLUE),
        ('米国株・ETF',          f"{df[df['cat3']=='米国株・ETF']['amount'].sum()/1e4:.1f}万円",
         'HDV / VTI / SPYD 等', ORANGE),
        ('米国債 利息',          f"{df[df['cat3']=='米国債利息']['amount'].sum()/1e4:.1f}万円",
         '4銘柄保有', PURPLE),
    ]
    gs = GridSpec(1,4,figure=fig,left=0.04,right=0.96,bottom=0.20,top=0.53,wspace=0.12)
    for i,(lbl,val,sub,clr) in enumerate(kpis):
        ax = fig.add_subplot(gs[0,i])
        ax.set_facecolor('#0C1E34')
        for sp in ax.spines.values(): sp.set_color(clr); sp.set_linewidth(2.5)
        ax.set_xticks([]); ax.set_yticks([])
        ax.text(0.5,0.80,lbl,ha='center',color='#8BB8D8',fontsize=9.5,
                transform=ax.transAxes)
        ax.text(0.5,0.50,val,ha='center',color=clr,fontsize=15,fontweight='bold',
                transform=ax.transAxes)
        if sub:
            ax.text(0.5,0.18,sub,ha='center',color='#4A6072',fontsize=9,
                    transform=ax.transAxes)

    fig.text(0.5,0.11,'個人投資ポートフォリオ分析   作成: 2026年6月27日',
             ha='center',color='#3A5A7A',fontsize=9)
    return fig

# ══════════════════════════════════════════════════════════════
# 2. 年別推移
# ══════════════════════════════════════════════════════════════
def s2_annual():
    by_yc = df.groupby(['year','cat3'])['amount'].sum().unstack(fill_value=0)
    for c in ['日本株','米国株・ETF','米国債利息']:
        if c not in by_yc.columns: by_yc[c]=0
    total_y = df.groupby('year')['amount'].sum()

    fig = make_slide('年別 配当金 推移と合計',
        f"累計 {df['amount'].sum()/1e4:.1f}万円（税引後）  ／  2025年が最高（{total_y.get(2025,0)/1e4:.1f}万円）")

    gs = GridSpec(2,2,figure=fig,left=0.06,right=0.97,
                  bottom=0.068,top=0.905,hspace=0.50,wspace=0.30)

    # 上段全幅: 積み上げ棒グラフ
    ax1 = fig.add_subplot(gs[0,:])
    xs = np.arange(len(YEARS)); bot = np.zeros(len(YEARS))
    for cat in ['日本株','米国株・ETF','米国債利息']:
        v = [by_yc.loc[y,cat]/1e4 if y in by_yc.index else 0 for y in YEARS]
        ax1.bar(xs,v,0.60,bottom=bot,color=CAT_C[cat],edgecolor=BG,lw=1.1,label=cat,zorder=3)
        bot += np.array(v)
    mx = total_y.max()/1e4
    for i,y in enumerate(YEARS):
        t = total_y.get(y,0)/1e4
        ax1.text(i, t+mx*0.02, f'{t:.1f}万', ha='center', fontsize=9.5,
                 fontweight='bold', color=NAVY)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([ylbl(y) for y in YEARS],fontsize=10)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.0f}万'))
    ax1.legend(fontsize=10,loc='upper left',framealpha=0.95,edgecolor=BORDER)
    chart_style(ax1,'年別 カテゴリ別 配当合計','万円')

    # 左下: 水平積み上げ棒（通年のみ）
    ax2 = fig.add_subplot(gs[1,0])
    fy = [y for y in YEARS if y not in (2021,2026)]
    bot2 = np.zeros(len(fy))
    for cat in ['日本株','米国株・ETF','米国債利息']:
        v = [by_yc.loc[y,cat]/1e4 if y in by_yc.index else 0 for y in fy]
        ax2.barh(range(len(fy)),v,0.60,left=bot2,color=CAT_C[cat],
                 edgecolor=BG,lw=0.8,label=cat,zorder=3)
        bot2 += np.array(v)
    ax2.set_yticks(range(len(fy)))
    ax2.set_yticklabels([str(y) for y in fy],fontsize=10)
    ax2.invert_yaxis()
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.0f}万'))
    ax2.grid(axis='x',color=BORDER,lw=0.7,alpha=0.9,zorder=0)
    ax2.spines[['top','right']].set_visible(False)
    ax2.spines[['left','bottom']].set_color(BORDER)
    ax2.tick_params(colors='#374151',labelsize=9.5)
    ax2.set_facecolor('#FAFBFD')
    ax2.set_title('通年比較（2022〜2025）',fontsize=11,fontweight='bold',color=NAVY,pad=7,loc='left')

    # 右下: 年別合計テーブル
    ax3 = fig.add_subplot(gs[1,1])
    ax3.set_title('年別合計（万円）',fontsize=11,fontweight='bold',color=NAVY,pad=7,loc='left')
    hdrs = ['年','日本株','米国ETF','米国債','合計']
    rows = []
    for y in YEARS:
        jp = by_yc.loc[y,'日本株'] if y in by_yc.index else 0
        us = by_yc.loc[y,'米国株・ETF'] if y in by_yc.index else 0
        bd = by_yc.loc[y,'米国債利息'] if y in by_yc.index else 0
        tag = '※' if y in (2021,2026) else ''
        rows.append([f'{y}{tag}',f'{jp/1e4:.1f}',f'{us/1e4:.1f}',
                     f'{bd/1e4:.1f}',f'{(jp+us+bd)/1e4:.1f}'])
    make_table(ax3, hdrs, rows, col_w=[0.22,0.20,0.20,0.20,0.18], scale=1.65)

    footer_text(fig,'※2021年は9月から、2026年は6月26日までの部分データです。')
    return fig

# ══════════════════════════════════════════════════════════════
# 3. 月別パターン
# ══════════════════════════════════════════════════════════════
def s3_monthly():
    MJ = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    key_m = [3,5,6,9,11,12]

    fig = make_slide('月別 配当受取パターン',
        '6・12月: 日本株決算  ／  3・6・9・12月: 米国ETF四半期  ／  5・11月: 米国債利息',
        accent=ORANGE)

    gs = GridSpec(2,2,figure=fig,left=0.06,right=0.97,
                  bottom=0.068,top=0.905,hspace=0.52,wspace=0.30)

    # 左上: 全期間月別
    ax1 = fig.add_subplot(gs[0,0])
    xs = np.arange(12); bot = np.zeros(12)
    for cat in ['日本株','米国株・ETF','米国債利息']:
        v = [df[df['cat3']==cat][df['month']==m+1]['amount'].sum()/1e4 for m in range(12)]
        ax1.bar(xs,v,0.70,bottom=bot,color=CAT_C[cat],edgecolor=BG,lw=0.8,label=cat,zorder=3)
        bot += np.array(v)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([m[:2] for m in MJ],fontsize=10)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.0f}万'))
    ax1.legend(fontsize=9,loc='upper right',framealpha=0.92,edgecolor=BORDER)
    chart_style(ax1,'全期間 月別累計','万円')

    # 右上: 2025年月別
    ax2 = fig.add_subplot(gs[0,1])
    df25 = df[df['year']==2025]; bot2 = np.zeros(12)
    for cat in ['日本株','米国株・ETF','米国債利息']:
        v = [df25[df25['cat3']==cat][df25['month']==m+1]['amount'].sum()/1e4 for m in range(12)]
        ax2.bar(xs,v,0.70,bottom=bot2,color=CAT_C[cat],edgecolor=BG,lw=0.8,label=cat,zorder=3)
        bot2 += np.array(v)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([m[:2] for m in MJ],fontsize=10)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.1f}万'))
    ax2.legend(fontsize=9,loc='upper right',framealpha=0.92,edgecolor=BORDER)
    chart_style(ax2,'2025年 月別内訳','万円')

    # 下段全幅: 主要月テーブル
    ax3 = fig.add_subplot(gs[1,:])
    ax3.set_title('主要入金月 × 年別配当（万円）',fontsize=11,fontweight='bold',color=NAVY,pad=7,loc='left')
    hdrs = ['月'] + [str(y) for y in YEARS] + ['合計','比率']
    tot_all = df['amount'].sum()
    rows = []
    for m in key_m:
        mt = df[df['month']==m]['amount'].sum()
        yv = [df[(df['year']==y)&(df['month']==m)]['amount'].sum() for y in YEARS]
        rows.append([f'{m}月']+[f'{v/1e4:.1f}' if v>0 else '—' for v in yv]+
                    [f'{mt/1e4:.1f}万',f'{mt/tot_all*100:.1f}%'])
    nc = 1+len(YEARS)+2
    cw = [0.07]+[0.11]*len(YEARS)+[0.10,0.08]
    s  = sum(cw); cw = [w/s for w in cw]
    make_table(ax3, hdrs, rows, col_w=cw, scale=1.6)

    footer_text(fig,'6・12月の日本株と3・6・9・12月の米国ETFが配当収入の大部分を占める。')
    return fig

# ══════════════════════════════════════════════════════════════
# 4. 日本株
# ══════════════════════════════════════════════════════════════
def s4_jp():
    jp = df[df['cat3']=='日本株']
    by_ny = jp.groupby(['name','year'])['amount'].sum().unstack(fill_value=0)
    for y in YEARS:
        if y not in by_ny.columns: by_ny[y]=0
    by_ny = by_ny[sorted(by_ny.columns)]
    tots  = by_ny.sum(axis=1).sort_values(ascending=False)
    top8  = tots.head(8).index.tolist()

    fig = make_slide('日本株 銘柄別・年別 配当推移',
        f"日本株累計: {jp['amount'].sum()/1e4:.1f}万円  ／  上位8銘柄")

    gs = GridSpec(2,2,figure=fig,left=0.06,right=0.97,
                  bottom=0.068,top=0.905,hspace=0.50,wspace=0.30)

    # 左上: 累計水平棒グラフ
    ax1 = fig.add_subplot(gs[0,0])
    ns = top8[::-1]; vs = [tots[n]/1e4 for n in ns]
    clrs = [BLUE if i>=len(ns)-3 else '#5BA4E3' for i in range(len(ns))]
    ax1.barh(range(len(ns)),vs,color=clrs,edgecolor=BG,height=0.65,lw=0.8,zorder=3)
    ax1.set_yticks(range(len(ns))); ax1.set_yticklabels(ns,fontsize=10)
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.0f}万'))
    mv = max(vs)
    for i,v in enumerate(vs):
        ax1.text(v+mv*0.025,i,f'{v:.1f}万',va='center',fontsize=9,
                 fontweight='bold',color=NAVY)
    ax1.set_xlim(0,mv*1.28)
    ax1.grid(axis='x',color=BORDER,lw=0.7,alpha=0.9,zorder=0)
    ax1.set_facecolor('#FAFBFD')
    ax1.spines[['top','right']].set_visible(False)
    ax1.spines[['left','bottom']].set_color(BORDER)
    ax1.tick_params(colors='#374151',labelsize=9.5)
    ax1.set_title('累計ランキング（上位8銘柄）',fontsize=11,fontweight='bold',color=NAVY,pad=7,loc='left')

    # 右上: 年次折れ線（上位5）
    ax2 = fig.add_subplot(gs[0,1])
    lc = [BLUE,'#4AA8E8',GREEN,ORANGE,PURPLE]
    for name,clr in zip(top8[:5],lc):
        yv = [by_ny.loc[name,y]/1e4 if name in by_ny.index else 0 for y in YEARS]
        ax2.plot(YEARS,yv,'o-',color=clr,lw=2,ms=6,label=name,zorder=3)
        if yv[-1]>0:
            ax2.annotate(f'{yv[-1]:.1f}万',xy=(YEARS[-1],yv[-1]),
                         xytext=(5,0),textcoords='offset points',
                         fontsize=8.5,color=clr,va='center',fontweight='bold')
    ax2.set_xticks(YEARS)
    ax2.set_xticklabels([str(y) for y in YEARS],fontsize=9,rotation=25,ha='right')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.1f}万'))
    ax2.legend(fontsize=9,framealpha=0.95,edgecolor=BORDER,ncol=2)
    chart_style(ax2,'上位5銘柄 年次推移','万円')

    # 下段全幅: テーブル（直近4年のみ表示）
    ax3 = fig.add_subplot(gs[1,:])
    ax3.set_title('銘柄別 年間配当（万円・直近4年）',fontsize=11,fontweight='bold',color=NAVY,pad=7,loc='left')
    show_y = [y for y in YEARS if y>=2023]
    hdrs = ['銘柄','累計']+[str(y) for y in show_y]+['前年比','傾向']
    rows = []
    for n in top8:
        cum = tots[n]
        v24 = by_ny.loc[n,2024] if (n in by_ny.index and 2024 in by_ny.columns) else 0
        v25 = by_ny.loc[n,2025] if (n in by_ny.index and 2025 in by_ny.columns) else 0
        yoy = f'{(v25/v24-1)*100:+.0f}%' if v24>0 else '—'
        tr  = '↑' if v25>v24*1.05 else '↓' if v25<v24*0.95 else '→'
        yv  = [f'{by_ny.loc[n,y]/1e4:.1f}' if (n in by_ny.index and y in by_ny.columns) else '—'
               for y in show_y]
        rows.append([n,f'{cum/1e4:.1f}']+yv+[yoy,tr])
    cw = [0.17,0.09]+[0.13]*len(show_y)+[0.09,0.07]
    s = sum(cw); cw = [w/s for w in cw]
    make_table(ax3,hdrs,rows,col_w=cw,scale=1.55)

    jp25=jp[jp['year']==2025]['amount'].sum()
    jp24=jp[jp['year']==2024]['amount'].sum()
    footer_text(fig,f"2025年 日本株配当合計: {jp25/1e4:.1f}万円（前年比 {(jp25/jp24-1)*100:+.0f}%）。")
    return fig

# ══════════════════════════════════════════════════════════════
# 5. 米国株・ETF・米国債
# ══════════════════════════════════════════════════════════════
def s5_us():
    us_df = df[df['cat3']!='日本株']
    by_ny = us_df.groupby(['name','year'])['amount'].sum().unstack(fill_value=0)
    for y in YEARS:
        if y not in by_ny.columns: by_ny[y]=0
    by_ny = by_ny[sorted(by_ny.columns)]
    tots  = by_ny.sum(axis=1).sort_values(ascending=False)

    etfs  = [n for n in ['HDV','VTI','SPYD','META'] if n in by_ny.index]
    bonds = [n for n in by_ny.index if '米国債' in n]
    ec    = [ORANGE,'#4AA8E8',GREEN,PURPLE]
    bc    = [PURPLE,'#9B59B6','#D35400','#E74C3C']

    fig = make_slide('米国株・ETF・米国債 銘柄別配当推移',
        f"米国ETF: {df[df['cat3']=='米国株・ETF']['amount'].sum()/1e4:.1f}万円  "
        f"／  米国債: {df[df['cat3']=='米国債利息']['amount'].sum()/1e4:.1f}万円（税引後）",
        accent=ORANGE)

    gs = GridSpec(2,2,figure=fig,left=0.06,right=0.97,
                  bottom=0.068,top=0.905,hspace=0.50,wspace=0.30)

    # 左上: ETF棒グラフ
    ax1 = fig.add_subplot(gs[0,0])
    ny = len(YEARS); bw = 0.68/max(len(etfs),1)
    for ti,(n,clr) in enumerate(zip(etfs,ec)):
        offs = np.arange(ny)-0.34+(ti+0.5)*bw
        ax1.bar(offs,[by_ny.loc[n,y]/1e4 for y in YEARS],bw*0.85,
                color=clr,edgecolor=BG,lw=0.8,label=n,zorder=3)
    ax1.set_xticks(np.arange(ny))
    ax1.set_xticklabels([ylbl(y) for y in YEARS],fontsize=9,rotation=20,ha='right')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.1f}万'))
    ax1.legend(fontsize=9.5,framealpha=0.95,edgecolor=BORDER)
    chart_style(ax1,'米国ETF・株 年別配当','万円')

    # 右上: 米国債棒グラフ
    ax2 = fig.add_subplot(gs[0,1])
    bw2 = 0.68/max(len(bonds),1)
    for bi,(n,clr) in enumerate(zip(bonds,bc)):
        offs = np.arange(ny)-0.34+(bi+0.5)*bw2
        ax2.bar(offs,[by_ny.loc[n,y]/1e4 for y in YEARS],bw2*0.85,
                color=clr,edgecolor=BG,lw=0.8,label=n,zorder=3)
    ax2.set_xticks(np.arange(ny))
    ax2.set_xticklabels([ylbl(y) for y in YEARS],fontsize=9,rotation=20,ha='right')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.1f}万'))
    ax2.legend(fontsize=8.5,framealpha=0.95,edgecolor=BORDER)
    chart_style(ax2,'米国債 年別利息収入','万円')

    # 下段全幅: テーブル
    ax3 = fig.add_subplot(gs[1,:])
    ax3.set_title('銘柄別 年間配当（万円・直近4年）',fontsize=11,fontweight='bold',color=NAVY,pad=7,loc='left')
    show_y = [y for y in YEARS if y>=2023]
    hdrs = ['銘柄','区分','累計']+[str(y) for y in show_y]+['前年比']
    rows = []
    for n in tots.index:
        cat_m = us_df[us_df['name']==n]['cat3'].mode()
        cat_s = 'ETF' if (len(cat_m)>0 and cat_m[0]=='米国株・ETF') else '米国債'
        cum = tots[n]
        v24 = by_ny.loc[n,2024] if 2024 in by_ny.columns else 0
        v25 = by_ny.loc[n,2025] if 2025 in by_ny.columns else 0
        yoy = f'{(v25/v24-1)*100:+.0f}%' if v24>0 else '—'
        yv  = [f'{by_ny.loc[n,y]/1e4:.1f}' if y in by_ny.columns else '—' for y in show_y]
        rows.append([n,cat_s,f'{cum/1e4:.1f}']+yv+[yoy])
    cw = [0.16,0.08,0.09]+[0.13]*len(show_y)+[0.09]
    s = sum(cw); cw=[w/s for w in cw]
    make_table(ax3,hdrs,rows,col_w=cw,scale=1.55)

    h25=df[(df['name']=='HDV')&(df['year']==2025)]['amount'].sum()
    h24=df[(df['name']=='HDV')&(df['year']==2024)]['amount'].sum()
    footer_text(fig,f"HDV 2025年: {h25/1e4:.1f}万円（前年比 {(h25/h24-1)*100:+.0f}%）。米国債4.250%は2025年6月満期・償還済み。")
    return fig

# ══════════════════════════════════════════════════════════════
# 6. 累計ランキング
# ══════════════════════════════════════════════════════════════
def s6_ranking():
    by_name = df.groupby('name')['amount'].sum().sort_values(ascending=False)
    by_year = df.groupby('year')['amount'].sum()
    fy = [y for y in YEARS if y not in (2021,2026)]

    fig = make_slide('全銘柄 累計配当ランキング',
        f"全{len(by_name)}銘柄  ／  累計総額: {df['amount'].sum()/1e4:.1f}万円（税引後）  ／  上位20銘柄",
        accent=GOLD)

    gs = GridSpec(2,2,figure=fig,left=0.04,right=0.97,
                  bottom=0.068,top=0.905,hspace=0.42,wspace=0.32)

    # 左全体: 水平棒（上位20）
    ax1 = fig.add_subplot(gs[:,0])
    ns  = by_name.index[:20].tolist()[::-1]
    vs  = [by_name[n]/1e4 for n in ns]
    def ncat(n):
        m=df[df['name']==n]['cat3'].mode()
        return BLUE if len(m)>0 and m[0]=='日本株' else ORANGE if len(m)>0 and m[0]=='米国株・ETF' else PURPLE
    bars = ax1.barh(range(len(ns)),vs,color=[ncat(n) for n in ns],
                    edgecolor=BG,height=0.68,lw=0.8,zorder=3)
    ax1.set_yticks(range(len(ns))); ax1.set_yticklabels(ns,fontsize=9.5)
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.0f}万'))
    mv = max(vs)
    for b,v in zip(bars,vs):
        ax1.text(b.get_width()+mv*0.02,b.get_y()+b.get_height()/2,
                 f'{v:.1f}万',va='center',fontsize=9,fontweight='bold',color=NAVY)
    ax1.set_xlim(0,mv*1.28)
    ax1.legend(handles=[mpatches.Patch(color=BLUE,label='日本株'),
                         mpatches.Patch(color=ORANGE,label='米国ETF'),
                         mpatches.Patch(color=PURPLE,label='米国債')],
               fontsize=9.5,loc='lower right',framealpha=0.95,edgecolor=BORDER)
    ax1.grid(axis='x',color=BORDER,lw=0.7,alpha=0.9,zorder=0)
    ax1.set_facecolor('#FAFBFD')
    ax1.spines[['top','right']].set_visible(False)
    ax1.spines[['left','bottom']].set_color(BORDER)
    ax1.tick_params(colors='#374151',labelsize=9.5)
    ax1.set_title('累計配当ランキング（上位20銘柄）',fontsize=11,fontweight='bold',color=NAVY,pad=7,loc='left')

    # 右上: 通年合計棒グラフ
    ax2 = fig.add_subplot(gs[0,1])
    fv = [by_year.get(y,0)/1e4 for y in fy]
    clr2 = [GOLD if v==max(fv) else BLUE for v in fv]
    b2 = ax2.bar(range(len(fy)),fv,color=clr2,edgecolor=BG,lw=0.8,width=0.60,zorder=3)
    ax2.set_xticks(range(len(fy)))
    ax2.set_xticklabels([str(y) for y in fy],fontsize=11)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.0f}万'))
    for b,v in zip(b2,fv):
        ax2.text(b.get_x()+b.get_width()/2,b.get_height()+0.5,
                 f'{v:.1f}万',ha='center',fontsize=10,fontweight='bold',color=NAVY)
    chart_style(ax2,'通年ベース 年別合計','万円')

    # 右下: 展望カード
    ax3 = fig.add_subplot(gs[1,1])
    ax3.set_facecolor('#F8FAFC')
    ax3.set_xlim(0,1); ax3.set_ylim(0,1); ax3.axis('off')
    ax3.add_patch(Rectangle((0,0),1,1,facecolor='#F8FAFC',
                              edgecolor=BORDER,lw=1,transform=ax3.transAxes))
    ax3.text(0.5,0.95,'今後の展望',ha='center',fontsize=11,fontweight='bold',
             color=NAVY,transform=ax3.transAxes)
    y26=by_year.get(2026,0)
    pts=[
        (BLUE,  '安定増配トレンド',  '三井物産・三菱UFJ等は連続増配継続。\n蔵王産業・JAC採用も高水準を維持。'),
        (ORANGE,'HDV NISA追加効果',  'NISA口座でのHDV積み増しにより\n非課税配当が拡大中。'),
        (PURPLE,'米国債4.250%満期', '2025年6月に償還完了。3銘柄体制。\n年間利息約15万円ペース継続。'),
        (GOLD,  '2026年受取ペース',  f'6/26時点で{y26/1e4:.1f}万円受取済み。\n年換算 約{y26/6*12/1e4:.0f}万円ペース。'),
    ]
    for i,(clr,title,desc) in enumerate(pts):
        iy = 0.80-i*0.21
        ax3.add_patch(Rectangle((0.03,iy-0.005),0.007,0.17,
                                  color=clr,transform=ax3.transAxes))
        ax3.text(0.06,iy+0.10,title,fontsize=9.5,fontweight='bold',
                 color=clr,transform=ax3.transAxes)
        ax3.text(0.06,iy+0.025,desc,fontsize=8.5,color='#374151',
                 transform=ax3.transAxes)

    y25=by_year.get(2025,0); y22=by_year.get(2022,0)
    footer_text(fig,f"累計 {df['amount'].sum()/1e4:.1f}万円。2025年最高 {y25/1e4:.1f}万円（2022年比 +{(y25/y22-1)*100:.0f}%）。")
    return fig

# ── 出力 ─────────────────────────────────────────────────────
OUT = "/Users/takahiroazuma/Desktop/kabu/claude/output/dividend_report_v3.pdf"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

slides = [s1_cover, s2_annual, s3_monthly, s4_jp, s5_us, s6_ranking]
A4W = int(297*150/25.4); A4H = int(210*150/25.4)
imgs = []
for i,fn in enumerate(slides):
    print(f"  {i+1}/{len(slides)}: {fn.__name__}")
    fig = fn()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    imgs.append(Image.open(buf).convert('RGB').resize((A4W,A4H),Image.LANCZOS))
    plt.close(fig)

imgs[0].save(OUT, save_all=True, append_images=imgs[1:], resolution=150)
print(f"\n✅  {OUT}  ({os.path.getsize(OUT)//1024} KB)")
