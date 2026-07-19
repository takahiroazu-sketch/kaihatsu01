#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配当金収入 分析レポート v2
DISTRIBUTION_20260619183952.csv (2021/8 - 2026/6/19)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
import re, io, os, csv, warnings
from PIL import Image
from datetime import datetime
warnings.filterwarnings('ignore')

# ─── フォント ────────────────────────────────────────────────────────────────
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
ORANGE = '#E67E22'; TEAL   = '#17A589'; BG     = '#F8FBFF'

# ─── CSV 読み込み ─────────────────────────────────────────────────────────────
CSV_PATH = "/Users/takahiroazuma/Desktop/kabu/claude/data/DISTRIBUTION_20260627095220.csv"

with open(CSV_PATH, encoding='cp932', errors='replace') as f:
    raw_lines = f.readlines()

records = []
for line in raw_lines:
    line = line.strip()
    if not line:
        continue
    try:
        row = list(csv.reader([line]))[0]
    except:
        continue
    if len(row) < 6:
        continue
    date_str = row[0]
    # ★修正: 月・日は1桁もOK（\d{1,2}）
    if not re.match(r'^20\d\d/\d{1,2}/\d{1,2}$', date_str):
        continue
    try:
        date   = datetime.strptime(date_str, '%Y/%m/%d')
        amount_str = row[5].replace(',', '').strip()
        if not amount_str:
            continue
        records.append({
            'date'    : date,
            'year'    : date.year,
            'month'   : date.month,
            'account' : row[1],
            'category': row[2],
            'name_raw': row[3],
            'amount'  : float(amount_str),
        })
    except:
        continue

print(f"読み込み件数: {len(records)} 件")

# ─── 銘柄名 正規化 ───────────────────────────────────────────────────────────
NAME_MAP = [
    # NTT (full-width & full name)
    ('ＮＴＴ',              'NTT'),
    ('日本電信電話',         'NTT'),
    ('ＫＤＤＩ',             'KDDI'),
    ('三井物産',             '三井物産'),
    ('蔵王産業',             '蔵王産業'),
    ('ジャックス',           'ジャックス'),
    ('オリックス',           'オリックス'),
    ('三菱ＵＦＪフィナンシャル', '三菱UFJ'),
    ('ジェイエイシーリクルートメント', 'JAC採用'),
    ('ＣＤＳ',               'CDS'),
    ('武田薬品工業',         '武田薬品'),
    ('三菱商事',             '三菱商事'),
    ('伊藤忠商事',           '伊藤忠'),
    ('バルカー',             'バルカー'),
    ('三井住友フィナンシャル', '三井住友FG'),
    ('東京海上ホールディングス', '東京海上'),
    ('第一生命ホールディングス', '第一生命'),
    ('第一ライフグループ',     '第一生命'),
    ('沖縄セルラー電話',     '沖縄セルラー'),
    ('三菱ＨＣキャピタル',   '三菱HC'),
    ('アサンテ',             'アサンテ'),
    ('アビスト',             'アビスト'),
    ('イー・ギャランティ',   'Eギャランティ'),
    ('信越化学工業',         '信越化学'),
    ('九州旅客鉄道',         'JR九州'),
    ('ソフトバンクグループ', 'SBG'),
    ('中国電力',             '中国電力'),
    # US ETF / Stocks
    ('バンガード トータルストックマーケット', 'VTI'),
    ('米国高配当株 ETF',     'HDV'),
    ('S&P500高配当株式ETF',  'SPYD'),
    ('S&P 500高配当株式ETF', 'SPYD'),
    ('メタ プラットフォームズ', 'META'),
    # US Bonds
    ('4.125',                '米国債4.125%'),
    ('4.750',                '米国債4.750%'),
    ('4.250',                '米国債4.250%'),
    ('4.000',                '米国債4.000%'),
]

def normalize(raw):
    for key, val in NAME_MAP:
        if key in raw:
            return val
    return re.sub(r'\s+\d{4}$', '', raw).strip()

for r in records:
    r['name'] = normalize(r['name_raw'])
    cat = r['category']
    r['cat3'] = ('日本株' if cat == '国内株式(現物)' else
                 '米国株・ETF' if cat == '米国株式' else '米国債利息')

df = pd.DataFrame(records)
YEARS = sorted(df['year'].unique())

# ─── データ確認 ──────────────────────────────────────────────────────────────
print("\n=== 年別合計 ===")
for y in YEARS:
    t = df[df['year']==y]['amount'].sum()
    tag = '(部分)' if y in (2021, 2026) else ''
    print(f"  {y}年{tag}: {t/1e4:.1f}万円")

print("\n=== NTT全データ ===")
ntt = df[df['name']=='NTT'][['year','month','amount']].sort_values(['year','month'])
print(ntt.to_string(index=False))

# ─── ユーティリティ ──────────────────────────────────────────────────────────
def new_fig(title="", subtitle="", tc=NAVY):
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=BG)
    if title:
        ah = fig.add_axes([0, 0.88, 1, 0.12])
        ah.set_facecolor(tc); ah.axis('off')
        ah.set_xlim(0, 1); ah.set_ylim(0, 1)
        ah.text(0.025, 0.65, title, color=WHITE, fontsize=20,
                fontweight='bold', va='center')
        if subtitle:
            ah.text(0.025, 0.18, subtitle, color='#AACCEE', fontsize=9, va='center')
        ah.axhline(0, color=GOLD, linewidth=3)
    return fig

def bbox(ax, x, y, w, h, edge, face, lw=1.5):
    r = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.010",
                       linewidth=lw, edgecolor=edge, facecolor=face,
                       transform=ax.transAxes)
    ax.add_patch(r)

def year_label(y):
    if y == 2021: return f"{y}年\n(8月〜)"
    if y == 2026: return f"{y}年\n(〜6/19)"
    return f"{y}年"

# ════════════════════════════════════════════════════════════════════════════
# スライド 1: 表紙
# ════════════════════════════════════════════════════════════════════════════
def slide_cover():
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=NAVY)
    ax  = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    for x, y, r, a in [(0.88,0.85,0.22,0.07), (0.08,0.12,0.16,0.05), (0.92,0.15,0.12,0.05)]:
        ax.add_patch(plt.Circle((x, y), r, color=BLUE, alpha=a))
    ax.axhline(0.44, color=GOLD, linewidth=4, xmin=0.05, xmax=0.95)
    ax.text(0.5, 0.83, "配当金収入 分析レポート", ha='center', color=WHITE,
            fontsize=32, fontweight='bold')
    ax.text(0.5, 0.70, "SBI証券   2021年9月〜2026年6月26日", ha='center', color=GOLD,
            fontsize=18, fontweight='bold')
    ax.text(0.5, 0.59, f"全{len(df)}件  |  2026年は6月26日時点の最新データまで反映", ha='center',
            color='#AACCEE', fontsize=11)

    total      = df['amount'].sum()
    jp_total   = df[df['cat3']=='日本株']['amount'].sum()
    us_total   = df[df['cat3']=='米国株・ETF']['amount'].sum()
    bond_total = df[df['cat3']=='米国債利息']['amount'].sum()

    kpis = [
        ("累計配当合計（税後）", f"{total/1e4:.1f}万円",  GOLD),
        ("日本株 配当",          f"{jp_total/1e4:.1f}万円", GREEN),
        ("米国株・ETF",          f"{us_total/1e4:.1f}万円", ORANGE),
        ("米国債 利息",          f"{bond_total/1e4:.1f}万円", PURPLE),
    ]
    for i, (lbl, val, clr) in enumerate(kpis):
        x = 0.06 + i * 0.22
        bbox(ax, x, 0.20, 0.20, 0.17, clr, '#1A3050', lw=2)
        ax.text(x+0.10, 0.353, lbl, ha='center', color='#AACCEE', fontsize=8.5)
        ax.text(x+0.10, 0.263, val, ha='center', color=clr,
                fontsize=13, fontweight='bold')
    ax.text(0.5, 0.10, "※ 2021年は9月から・2026年は6月26日までの部分データ",
            ha='center', color='#6688AA', fontsize=9)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 2: 年別配当合計 推移（カテゴリ別 + 合計テーブル）
# ════════════════════════════════════════════════════════════════════════════
def slide_annual():
    by_yc = df.groupby(['year','cat3'])['amount'].sum().unstack(fill_value=0)
    for c in ['日本株','米国株・ETF','米国債利息']:
        if c not in by_yc.columns:
            by_yc[c] = 0
    total_by_year = df.groupby('year')['amount'].sum()
    full_years = [y for y in YEARS if y not in (2021, 2026)]

    fig = new_fig("年別 配当金 推移と合計",
                  f"累計合計: {df['amount'].sum()/1e4:.1f}万円（税引後）  ｜  ※2021年:9月〜 / 2026年:〜6/26 は部分データ")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # KPIカード（通年ベース）
    best_y  = max(full_years, key=lambda y: total_by_year.get(y, 0))
    avg_full = np.mean([total_by_year.get(y, 0) for y in full_years])
    growth  = (total_by_year.get(2025,0)/total_by_year.get(2022,0)-1)*100 if total_by_year.get(2022,0) else 0
    kpis = [
        ("2025年 最高額",        f"{total_by_year.get(2025,0)/1e4:.1f}万円", GOLD),
        ("2024年",               f"{total_by_year.get(2024,0)/1e4:.1f}万円", BLUE),
        ("2022〜2025 年平均",    f"{avg_full/1e4:.1f}万円",                   GREEN),
        ("2022→2025 増加率",     f"+{growth:.0f}%",                          ORANGE),
    ]
    for i, (lbl, val, clr) in enumerate(kpis):
        x = 0.02 + i * 0.245
        bbox(ax, x, 0.73, 0.23, 0.13, clr, WHITE, lw=2)
        ax.text(x+0.115, 0.840, lbl, ha='center', fontsize=9, color=GRAY)
        ax.text(x+0.115, 0.782, val, ha='center', fontsize=14, fontweight='bold', color=clr)

    # 左: 積み上げ棒グラフ
    ax1 = fig.add_axes([0.03, 0.22, 0.52, 0.48])
    cats   = ['日本株','米国株・ETF','米国債利息']
    colors = [GREEN, ORANGE, PURPLE]
    xs = np.arange(len(YEARS))
    bottoms = np.zeros(len(YEARS))
    for cat, clr in zip(cats, colors):
        vals = [by_yc.loc[y, cat] if y in by_yc.index else 0 for y in YEARS]
        ax1.bar(xs, [v/1e4 for v in vals], 0.6, bottom=[b/1e4 for b in bottoms],
                color=clr, edgecolor='white', linewidth=1, label=cat)
        bottoms += np.array(vals)
    # 合計ラベル
    for i, y in enumerate(YEARS):
        tot = total_by_year.get(y, 0)
        ax1.text(i, tot/1e4 + 0.2, f'{tot/1e4:.1f}万', ha='center',
                 fontsize=8.5, fontweight='bold', color=NAVY)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([year_label(y) for y in YEARS], fontsize=8.5)
    ax1.set_ylabel('配当金（万円）', fontsize=9)
    ax1.set_title('年別 カテゴリ別 配当合計', fontsize=12, fontweight='bold')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.grid(axis='y', alpha=0.3); ax1.spines[['top','right']].set_visible(False)
    ax1.legend(fontsize=9, loc='upper left')

    # 右: 折れ線（カテゴリ別トレンド）
    ax2 = fig.add_axes([0.59, 0.22, 0.39, 0.48])
    for cat, clr in zip(cats, colors):
        vals = [by_yc.loc[y, cat] if y in by_yc.index else 0 for y in YEARS]
        style = '--' if cat == '米国債利息' else '-'
        ax2.plot(YEARS, [v/1e4 for v in vals], f'o{style}', color=clr,
                 lw=2, ms=6, label=cat)
        ax2.annotate(f'{vals[-1]/1e4:.1f}万', xy=(YEARS[-1], vals[-1]/1e4),
                     xytext=(4, 0), textcoords='offset points',
                     fontsize=8, color=clr, fontweight='bold', va='center')
    ax2.set_xticks(YEARS)
    ax2.set_xticklabels([str(y) for y in YEARS], fontsize=8, rotation=30)
    ax2.set_ylabel('万円', fontsize=9)
    ax2.set_title('カテゴリ別 年次推移', fontsize=11, fontweight='bold')
    ax2.grid(alpha=0.3); ax2.spines[['top','right']].set_visible(False)
    ax2.legend(fontsize=8)

    # 下部: 詳細テーブル
    col_xs = [0.02, 0.17, 0.29, 0.40, 0.51, 0.62, 0.73, 0.85]
    col_ws = [0.14, 0.12, 0.11, 0.11, 0.11, 0.11, 0.11, 0.13]
    hdrs   = ['', '2021年\n(9月〜)', '2022年', '2023年', '2024年', '2025年', '2026年\n(〜6/26)', '累計']

    for h, cx, cw in zip(hdrs, col_xs, col_ws):
        bbox(ax, cx, 0.155, cw-0.003, 0.048, NAVY, NAVY, lw=0)
        ax.text(cx+cw/2, 0.179, h, ha='center', va='center',
                fontsize=8, fontweight='bold', color=WHITE)

    row_items = [
        ('日本株',    GREEN,  'cat3', '日本株'),
        ('米国株・ETF', ORANGE, 'cat3', '米国株・ETF'),
        ('米国債利息', PURPLE, 'cat3', '米国債利息'),
        ('合計',      GOLD,   None,   None),
    ]
    for ri, (lbl, clr, col, val) in enumerate(row_items):
        ry   = 0.103 - ri * 0.046
        bg   = WHITE if ri % 2 == 0 else '#F5F8FF'
        if col:
            sub = df[df[col]==val]
        else:
            sub = df
        row_vals = [sub[sub['year']==y]['amount'].sum() for y in YEARS]
        total_row = sub['amount'].sum()

        all_vals = [lbl] + [f'{v/1e4:.1f}万' if v > 0 else '—' for v in row_vals] + [f'{total_row/1e4:.1f}万']
        for j, (v, cx, cw) in enumerate(zip(all_vals, col_xs, col_ws)):
            face = bg if j > 0 else '#EEF5FF'
            edge = '#CCDDEE'
            bbox(ax, cx, ry, cw-0.003, 0.042, edge, face, lw=0.5)
            fc = clr if j == 0 or j == len(all_vals)-1 else NAVY
            fw = 'bold' if j == 0 or j == len(all_vals)-1 else 'normal'
            ax.text(cx+cw/2, ry+0.021, str(v), ha='center', va='center',
                    fontsize=8, color=fc, fontweight=fw)

    bbox(ax, 0.02, 0.01, 0.96, 0.055, NAVY, NAVY, lw=0)
    ax.text(0.5, 0.048, f"2025年は年間{total_by_year.get(2025,0)/1e4:.1f}万円と過去最高。2022年比 +{growth:.0f}%の増加。2026年はすでに{total_by_year.get(2026,0)/1e4:.1f}万円を受取済み（6月19日時点）。",
            ha='center', fontsize=10, fontweight='bold', color=GOLD)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 3: 月別 受取パターン（棒グラフ）
# ════════════════════════════════════════════════════════════════════════════
def slide_monthly():
    MONTHS_JP = ['1月','2月','3月','4月','5月','6月',
                 '7月','8月','9月','10月','11月','12月']

    fig = new_fig("月別 配当受取パターン（全期間累計）",
                  "6月・12月に日本株が集中。3月・6月・9月・12月に米国ETFが四半期入金。全期間の月別合計を表示。")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    cats   = ['日本株','米国株・ETF','米国債利息']
    colors = [GREEN, ORANGE, PURPLE]

    # 上段: 月別カテゴリ積み上げ棒グラフ（全期間合計）
    ax1 = fig.add_axes([0.04, 0.41, 0.56, 0.44])
    xs = np.arange(12)
    bottoms = np.zeros(12)
    for cat, clr in zip(cats, colors):
        sub = df[df['cat3']==cat]
        vals = [sub[sub['month']==m]['amount'].sum() for m in range(1,13)]
        ax1.bar(xs, [v/1e4 for v in vals], 0.65, bottom=[b/1e4 for b in bottoms],
                color=clr, edgecolor='white', linewidth=0.8, label=cat)
        bottoms += np.array(vals)
    for i in range(12):
        tot = sum(df[df['month']==i+1]['amount'].sum() for _ in [None])
        if tot > 0:
            ax1.text(i, tot/1e4 + 0.3, f'{tot/1e4:.1f}万', ha='center',
                     fontsize=7.5, fontweight='bold', color=NAVY)
    ax1.set_xticks(xs)
    ax1.set_xticklabels(MONTHS_JP, fontsize=9)
    ax1.set_ylabel('累計配当（万円）', fontsize=9)
    ax1.set_title('月別 累計配当（全期間・カテゴリ別積み上げ）', fontsize=12, fontweight='bold')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.grid(axis='y', alpha=0.3); ax1.spines[['top','right']].set_visible(False)
    ax1.legend(fontsize=9, loc='upper right')

    # 右上: 2025年の月別推移（最新フル年）
    ax2 = fig.add_axes([0.65, 0.41, 0.33, 0.44])
    df25 = df[df['year']==2025]
    for cat, clr in zip(cats, colors):
        sub = df25[df25['cat3']==cat]
        vals = [sub[sub['month']==m]['amount'].sum() for m in range(1,13)]
        ax2.bar(xs, [v/1e4 for v in vals],
                0.65, color=clr, edgecolor='white', linewidth=0.8, label=cat)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([m[:2] for m in MONTHS_JP], fontsize=8)
    ax2.set_ylabel('万円', fontsize=9)
    ax2.set_title('2025年 月別配当内訳', fontsize=11, fontweight='bold')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax2.grid(axis='y', alpha=0.3); ax2.spines[['top','right']].set_visible(False)
    ax2.legend(fontsize=8)

    # 下段: 年別 × 月別 配当一覧テーブル（主要月のみ）
    key_months = [3, 5, 6, 9, 11, 12]
    ax.text(0.03, 0.375, "■ 年別・月別 配当合計（万円）　主要入金月", fontsize=10,
            fontweight='bold', color=NAVY)

    col_xs = [0.02, 0.14, 0.23, 0.32, 0.41, 0.50, 0.59, 0.68, 0.77]
    col_ws = [0.11, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.11]
    hdrs   = ['月', '2021年', '2022年', '2023年', '2024年', '2025年', '2026年', '合計', '比率']

    for h, cx, cw in zip(hdrs, col_xs, col_ws):
        bbox(ax, cx, 0.316, cw-0.003, 0.042, NAVY, NAVY, lw=0)
        ax.text(cx+cw/2, 0.337, h, ha='center', va='center',
                fontsize=8, fontweight='bold', color=WHITE)

    total_all = df['amount'].sum()
    for ri, m in enumerate(key_months):
        ry  = 0.274 - ri * 0.042
        bg  = '#EEF5FF' if ri % 2 == 0 else WHITE
        m_total = df[df['month']==m]['amount'].sum()
        y_vals  = [df[(df['year']==y)&(df['month']==m)]['amount'].sum() for y in YEARS]
        pct     = m_total / total_all * 100
        clr_m   = RED if m in (6, 12) else (ORANGE if m in (3, 9) else NAVY)

        row_vals = [f"{m}月"] + [f'{v/1e4:.1f}万' if v > 0 else '—' for v in y_vals] + \
                   [f'{m_total/1e4:.1f}万', f'{pct:.1f}%']
        for j, (v, cx, cw) in enumerate(zip(row_vals, col_xs, col_ws)):
            face = '#FFF0F0' if m in (6,12) else ('#FFF8EE' if m in (3,9) else bg)
            bbox(ax, cx, ry, cw-0.003, 0.038, '#CCDDEE', face, lw=0.3)
            fc  = clr_m if j == 0 else (RED if m in (6,12) and j == len(row_vals)-1 else NAVY)
            fw  = 'bold' if j == 0 or j >= len(row_vals)-2 else 'normal'
            ax.text(cx+cw/2, ry+0.019, str(v), ha='center', va='center',
                    fontsize=8, color=fc, fontweight=fw)

    # 6月と12月の注釈
    ax.text(0.03, 0.022, "■ 6月・12月は日本株の決算配当（年2回）が集中。  "
            "■ 3月・6月・9月・12月は米国ETF(HDV/VTI/SPYD)の四半期配当。  "
            "■ 5月・11月は米国債の半期利息。",
            fontsize=9, color=NAVY)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 4: 日本株 銘柄別 年別配当
# ════════════════════════════════════════════════════════════════════════════
def slide_jp():
    jp = df[df['cat3']=='日本株']
    by_ny = jp.groupby(['name','year'])['amount'].sum().unstack(fill_value=0)
    for y in YEARS:
        if y not in by_ny.columns:
            by_ny[y] = 0
    by_ny = by_ny[sorted(by_ny.columns)]
    totals = by_ny.sum(axis=1).sort_values(ascending=False)
    top_names = totals.head(12).index.tolist()

    fig = new_fig("日本株 銘柄別・年別 配当推移",
                  f"日本株 累計: {jp['amount'].sum()/1e4:.1f}万円（税引後）  ｜  上位12銘柄を表示")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # 左: 上位7銘柄 グループ棒グラフ
    top7   = top_names[:7]
    clrs7  = [BLUE,'#5DADE2',GREEN,'#52BE80',ORANGE,GOLD,PURPLE]
    ax1 = fig.add_axes([0.02, 0.40, 0.58, 0.46])
    n_y = len(YEARS); gw = 0.8; bw = gw / len(top7)
    for ti, (name, clr) in enumerate(zip(top7, clrs7)):
        offs = np.arange(n_y) - gw/2 + (ti+0.5)*bw
        vals = [by_ny.loc[name, y] if (name in by_ny.index and y in by_ny.columns) else 0
                for y in YEARS]
        ax1.bar(offs, [v/1e4 for v in vals], bw*0.88, color=clr,
                edgecolor='white', label=name, linewidth=0.6)
    ax1.set_xticks(np.arange(n_y))
    ax1.set_xticklabels([year_label(y) for y in YEARS], fontsize=8.5)
    ax1.set_ylabel('配当（万円）', fontsize=9)
    ax1.set_title('上位7銘柄 年別配当比較', fontsize=12, fontweight='bold')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.grid(axis='y', alpha=0.3); ax1.spines[['top','right']].set_visible(False)
    ax1.legend(fontsize=7.5, ncol=4, loc='upper left')

    # 右: 折れ線（上位4銘柄）
    ax2 = fig.add_axes([0.65, 0.40, 0.33, 0.46])
    for name, clr in zip(top_names[:4], [BLUE, GREEN, ORANGE, RED]):
        vals = [by_ny.loc[name, y] if (name in by_ny.index and y in by_ny.columns) else 0
                for y in YEARS]
        ax2.plot(YEARS, [v/1e4 for v in vals], 'o-', color=clr, lw=2, ms=5, label=name)
    ax2.set_xticks(YEARS)
    ax2.set_xticklabels([str(y)[2:] for y in YEARS], fontsize=8)
    ax2.set_ylabel('万円', fontsize=9)
    ax2.set_title('上位4銘柄 推移', fontsize=10, fontweight='bold')
    ax2.grid(alpha=0.3); ax2.spines[['top','right']].set_visible(False)
    ax2.legend(fontsize=8)

    # 下部: 全銘柄テーブル（上位12）
    ax.text(0.02, 0.365, "■ 銘柄別 年間配当一覧（万円・税引後）", fontsize=10,
            fontweight='bold', color=NAVY)
    col_xs = [0.02, 0.145, 0.245, 0.330, 0.415, 0.500, 0.585, 0.670, 0.790]
    col_ws = [0.123, 0.097, 0.083, 0.083, 0.083, 0.083, 0.083, 0.120, 0.115]
    hdrs   = ['銘柄', '累計', '2022年', '2023年', '2024年', '2025年', '2026年\n(〜6/26)', '前年比', '傾向']

    for h, cx, cw in zip(hdrs, col_xs, col_ws):
        bbox(ax, cx, 0.310, cw-0.003, 0.042, NAVY, NAVY, lw=0)
        ax.text(cx+cw/2, 0.331, h, ha='center', va='center',
                fontsize=7.5, fontweight='bold', color=WHITE)

    for ri, name in enumerate(top_names):
        ry   = 0.278 - ri * 0.026
        bg   = '#EEF5FF' if ri%2==0 else WHITE
        cumul = totals[name]
        v24 = by_ny.loc[name, 2024] if (name in by_ny.index and 2024 in by_ny.columns) else 0
        v25 = by_ny.loc[name, 2025] if (name in by_ny.index and 2025 in by_ny.columns) else 0
        v26 = by_ny.loc[name, 2026] if (name in by_ny.index and 2026 in by_ny.columns) else 0
        yoy = f'{(v25/v24-1)*100:+.0f}%' if v24 > 0 else '—'
        if   v25 > v24*1.05: trend, tc = '↑増加', GREEN
        elif v25 < v24*0.95: trend, tc = '↓減少', RED
        else:                 trend, tc = '→横ばい', GRAY

        row_vals = [
            name, f'{cumul/1e4:.1f}万',
            f'{by_ny.loc[name,2022]/1e4:.1f}万' if (name in by_ny.index and 2022 in by_ny.columns) else '—',
            f'{by_ny.loc[name,2023]/1e4:.1f}万' if (name in by_ny.index and 2023 in by_ny.columns) else '—',
            f'{v24/1e4:.1f}万' if v24 else '—',
            f'{v25/1e4:.1f}万' if v25 else '—',
            f'{v26/1e4:.1f}万' if v26 else '—',
            yoy, trend,
        ]
        for j, (v, cx, cw) in enumerate(zip(row_vals, col_xs, col_ws)):
            bbox(ax, cx, ry, cw-0.003, 0.023, '#CCDDEE', bg, lw=0.3)
            if j == 0:      fc, fw = BLUE,  'bold'
            elif j == 1:    fc, fw = GREEN, 'bold'
            elif j == 7:
                fc = GREEN if '+' in yoy else (RED if '-' in yoy else GRAY)
                fw = 'bold'
            elif j == 8:    fc, fw = tc, 'bold'
            else:           fc, fw = NAVY, 'normal'
            ax.text(cx+cw/2, ry+0.0115, str(v), ha='center', va='center',
                    fontsize=7.5, color=fc, fontweight=fw)

    bbox(ax, 0.02, 0.01, 0.96, 0.055, GREEN, GREEN, lw=0)
    jp25 = jp[jp['year']==2025]['amount'].sum()
    jp24 = jp[jp['year']==2024]['amount'].sum()
    ax.text(0.5, 0.048, f"2025年 日本株配当: {jp25/1e4:.1f}万円（前年比 {(jp25/jp24-1)*100:+.0f}%）。"
            "蔵王産業・JACリクルート・三井物産が上位を占める。2026年（〜6/26）は入金ラッシュ中。",
            ha='center', fontsize=9.5, fontweight='bold', color=WHITE)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 5: 米国株・ETF・米国債 銘柄別推移
# ════════════════════════════════════════════════════════════════════════════
def slide_us():
    us = df[df['cat3'] != '日本株']
    by_ny = us.groupby(['name','year'])['amount'].sum().unstack(fill_value=0)
    for y in YEARS:
        if y not in by_ny.columns:
            by_ny[y] = 0
    by_ny = by_ny[sorted(by_ny.columns)]
    totals_us = by_ny.sum(axis=1).sort_values(ascending=False)

    etf_names  = [n for n in ['HDV','VTI','SPYD','META'] if n in by_ny.index]
    bond_names = [n for n in by_ny.index if '米国債' in n]

    fig = new_fig("米国株・ETF・米国債 銘柄別配当推移",
                  f"米国株・ETF累計: {df[df['cat3']=='米国株・ETF']['amount'].sum()/1e4:.1f}万円  ｜  "
                  f"米国債利息累計: {df[df['cat3']=='米国債利息']['amount'].sum()/1e4:.1f}万円（税引後）",
                  tc='#6C3483')
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    etf_colors  = {n: c for n,c in zip(['HDV','VTI','SPYD','META'],
                                         [ORANGE, BLUE, GREEN, RED])}
    bond_colors = [PURPLE,'#9B59B6','#A569BD','#BB8FCE']

    # 左上: ETF 年別グループ棒グラフ
    ax1 = fig.add_axes([0.03, 0.46, 0.44, 0.40])
    n_y = len(YEARS)
    gw  = 0.8; bw = gw / max(len(etf_names), 1)
    for ti, name in enumerate(etf_names):
        offs = np.arange(n_y) - gw/2 + (ti+0.5)*bw
        vals = [by_ny.loc[name, y] for y in YEARS]
        ax1.bar(offs, [v/1e4 for v in vals], bw*0.88,
                color=etf_colors.get(name, GRAY),
                edgecolor='white', label=name, linewidth=0.6)
    ax1.set_xticks(np.arange(n_y))
    ax1.set_xticklabels([year_label(y) for y in YEARS], fontsize=8)
    ax1.set_ylabel('万円', fontsize=9)
    ax1.set_title('米国ETF・株 年別配当', fontsize=11, fontweight='bold')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.grid(axis='y', alpha=0.3); ax1.spines[['top','right']].set_visible(False)
    ax1.legend(fontsize=9, loc='upper left')

    # 右上: 米国債 年別棒グラフ
    ax2 = fig.add_axes([0.52, 0.46, 0.46, 0.40])
    bond_xs = np.arange(len(YEARS))
    bw_bond = 0.8 / max(len(bond_names), 1)
    for bi, (name, clr) in enumerate(zip(bond_names, bond_colors)):
        offs = bond_xs - 0.4 + (bi+0.5)*bw_bond
        vals = [by_ny.loc[name, y] for y in YEARS]
        ax2.bar(offs, [v/1e4 for v in vals], bw_bond*0.88,
                color=clr, edgecolor='white', label=name, linewidth=0.6)
    ax2.set_xticks(bond_xs)
    ax2.set_xticklabels([year_label(y) for y in YEARS], fontsize=8)
    ax2.set_ylabel('万円', fontsize=9)
    ax2.set_title('米国債 年別利息収入', fontsize=11, fontweight='bold')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax2.grid(axis='y', alpha=0.3); ax2.spines[['top','right']].set_visible(False)
    ax2.legend(fontsize=8)

    # 下部テーブル（全銘柄）
    ax.text(0.02, 0.415, "■ 銘柄別 年間配当一覧（万円・税引後）", fontsize=10,
            fontweight='bold', color='#6C3483')
    col_xs = [0.02, 0.185, 0.285, 0.370, 0.455, 0.540, 0.625, 0.710, 0.820]
    col_ws = [0.163, 0.098, 0.083, 0.083, 0.083, 0.083, 0.083, 0.110, 0.115]
    hdrs   = ['銘柄', '累計', '2022年', '2023年', '2024年', '2025年', '2026年(〜6/26)', '前年比', '傾向']

    for h, cx, cw in zip(hdrs, col_xs, col_ws):
        bbox(ax, cx, 0.357, cw-0.003, 0.042, PURPLE, PURPLE, lw=0)
        ax.text(cx+cw/2, 0.378, h, ha='center', va='center',
                fontsize=7.5, fontweight='bold', color=WHITE)

    all_us_names = totals_us.index.tolist()
    for ri, name in enumerate(all_us_names):
        ry   = 0.326 - ri * 0.031
        bg   = '#F3E8FF' if ri%2==0 else WHITE
        cumul = totals_us[name]
        v24 = by_ny.loc[name, 2024] if 2024 in by_ny.columns else 0
        v25 = by_ny.loc[name, 2025] if 2025 in by_ny.columns else 0
        v26 = by_ny.loc[name, 2026] if 2026 in by_ny.columns else 0
        yoy = f'{(v25/v24-1)*100:+.0f}%' if v24 > 0 else '—'
        if   v25 > v24*1.05: trend, tc = '↑増加', GREEN
        elif v25 < v24*0.95: trend, tc = '↓減少', RED
        else:                 trend, tc = '→横ばい', GRAY
        row_vals = [
            name, f'{cumul/1e4:.1f}万',
            f'{by_ny.loc[name,2022]/1e4:.1f}万' if 2022 in by_ny.columns else '—',
            f'{by_ny.loc[name,2023]/1e4:.1f}万' if 2023 in by_ny.columns else '—',
            f'{v24/1e4:.1f}万' if v24 else '—',
            f'{v25/1e4:.1f}万' if v25 else '—',
            f'{v26/1e4:.1f}万' if v26 else '—',
            yoy, trend,
        ]
        for j, (v, cx, cw) in enumerate(zip(row_vals, col_xs, col_ws)):
            bbox(ax, cx, ry, cw-0.003, 0.027, '#CCAAEE', bg, lw=0.3)
            if j == 0:   fc, fw = PURPLE, 'bold'
            elif j == 1: fc, fw = ORANGE, 'bold'
            elif j == 7:
                fc = GREEN if '+' in yoy else (RED if '-' in yoy else GRAY)
                fw = 'bold'
            elif j == 8: fc, fw = tc, 'bold'
            else:        fc, fw = NAVY, 'normal'
            ax.text(cx+cw/2, ry+0.0135, str(v), ha='center', va='center',
                    fontsize=7.5, color=fc, fontweight=fw)

    bbox(ax, 0.02, 0.01, 0.96, 0.055, PURPLE, PURPLE, lw=0)
    hdv25 = df[(df['name']=='HDV')&(df['year']==2025)]['amount'].sum()
    hdv24 = df[(df['name']=='HDV')&(df['year']==2024)]['amount'].sum()
    ax.text(0.5, 0.048, f"HDVは2025年: {hdv25/1e4:.1f}万円（前年比{(hdv25/hdv24-1)*100:+.0f}%）。"
            "NISA枠追加（88株）で非課税分が加算。米国債4.250%は2025年6月に満期済み。",
            ha='center', fontsize=9.5, fontweight='bold', color=WHITE)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 6: 全銘柄 累計ランキング
# ════════════════════════════════════════════════════════════════════════════
def slide_ranking():
    by_name = df.groupby('name')['amount'].sum().sort_values(ascending=False)
    by_year = df.groupby('year')['amount'].sum()

    fig = new_fig("全銘柄 累計配当ランキング",
                  f"全{len(by_name)}銘柄  ｜  累計配当総額: {df['amount'].sum()/1e4:.1f}万円（税引後）  ｜  上位20位を表示")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # 左: 水平棒グラフ（上位20）
    ax1 = fig.add_axes([0.03, 0.09, 0.52, 0.78])
    names20 = by_name.index[:20].tolist()
    vals20  = [by_name[n] for n in names20]
    cat_clr = {}
    for n in names20:
        m = df[df['name']==n]['cat3'].mode()
        cat_clr[n] = GREEN if (len(m)>0 and m[0]=='日本株') else \
                     ORANGE if (len(m)>0 and m[0]=='米国株・ETF') else PURPLE
    bars = ax1.barh(range(len(names20)), [v/1e4 for v in vals20],
                    color=[cat_clr[n] for n in names20],
                    edgecolor='white', height=0.7)
    ax1.set_yticks(range(len(names20)))
    ax1.set_yticklabels(names20, fontsize=9)
    ax1.invert_yaxis()
    ax1.set_xlabel('累計配当（万円）', fontsize=9)
    ax1.set_title('全銘柄 累計配当ランキング（上位20）', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3); ax1.spines[['top','right']].set_visible(False)
    for bar, val in zip(bars, vals20):
        ax1.text(bar.get_width()+0.4, bar.get_y()+bar.get_height()/2,
                 f'{val/1e4:.1f}万', va='center', fontsize=8, fontweight='bold')
    ax1.set_xlim(0, max(vals20)/1e4 * 1.22)
    patches_leg = [mpatches.Patch(color=GREEN, label='日本株'),
                   mpatches.Patch(color=ORANGE, label='米国株・ETF'),
                   mpatches.Patch(color=PURPLE, label='米国債利息')]
    ax1.legend(handles=patches_leg, fontsize=9, loc='lower right')

    # 右上: 通年 年別合計
    ax2 = fig.add_axes([0.60, 0.51, 0.38, 0.36])
    full_years = [y for y in YEARS if y not in (2021, 2026)]
    fy_vals    = [by_year.get(y, 0)/1e4 for y in full_years]
    bar_clrs   = [GOLD if v == max(fy_vals) else BLUE for v in fy_vals]
    bars2 = ax2.bar(range(len(full_years)), fy_vals, color=bar_clrs,
                    edgecolor='white', linewidth=1.2, width=0.6)
    ax2.set_xticks(range(len(full_years)))
    ax2.set_xticklabels([str(y) for y in full_years], fontsize=10)
    ax2.set_ylabel('万円', fontsize=9)
    ax2.set_title('通年ベース 年別合計', fontsize=11, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3); ax2.spines[['top','right']].set_visible(False)
    for bar, val in zip(bars2, fy_vals):
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                 f'{val:.1f}万', ha='center', fontsize=9, fontweight='bold', color=NAVY)

    # 右下: 展望カード
    ax.text(0.60, 0.468, "■ 将来展望・ポイント", fontsize=11, fontweight='bold', color=NAVY)
    insights = [
        (GREEN,  "安定増配トレンド",
         "三井物産・三菱UFJ等は2022年以降連続\n増配。蔵王産業も高水準を維持。"),
        (ORANGE, "HDV NISA追加の効果",
         "NISA枠88株追加で2025年から非課税分が\n加算。年間配当が実質的に増加。"),
        (PURPLE, "米国債4.250%は満期済み",
         "2025年6月満期・償還完了。以降は\n3銘柄体制。年間利息は約15万円ペース。"),
        (GOLD,   "2026年（〜6/26）: 39.5万円",
         "蔵王・武田・三菱商事・HDV・SPYDも入金済み。\n年換算で約79万円ペースで推移中。"),
    ]
    for i, (clr, title, desc) in enumerate(insights):
        y_pos = 0.41 - i * 0.102
        bbox(ax, 0.59, y_pos, 0.40, 0.088, clr, '#FAFCFF', lw=1.5)
        ax.text(0.605, y_pos+0.060, f"● {title}", fontsize=9.5, fontweight='bold', color=clr)
        ax.text(0.605, y_pos+0.012, desc, fontsize=8.5, color=GRAY)

    bbox(ax, 0.02, 0.01, 0.96, 0.055, NAVY, NAVY, lw=0)
    y25 = by_year.get(2025, 0); y22 = by_year.get(2022, 0)
    y26 = by_year.get(2026, 0)
    ax.text(0.5, 0.048,
            f"累計 {df['amount'].sum()/1e4:.1f}万円。2025年: {y25/1e4:.1f}万（2022年比 +{(y25/y22-1)*100:.0f}%）。"
            f"2026年は6/19時点で {y26/1e4:.1f}万円、年換算で約{y26/6*12/1e4:.0f}万円ペース。",
            ha='center', fontsize=10, fontweight='bold', color=GOLD)
    return fig

# ─── PDF 出力 ─────────────────────────────────────────────────────────────────
OUTPUT_DIR  = "/Users/takahiroazuma/Desktop/kabu/claude/output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dividend_report.pdf")
os.makedirs(OUTPUT_DIR, exist_ok=True)

slides = [slide_cover, slide_annual, slide_monthly,
          slide_jp, slide_us, slide_ranking]

A4_W = int(297 * 150 / 25.4)
A4_H = int(210 * 150 / 25.4)

print("\n配当金分析レポート PDF を生成中...")
pil_images = []
for i, fn in enumerate(slides):
    print(f"  スライド {i+1}/{len(slides)}: {fn.__name__}")
    fig = fn()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).convert('RGB').resize((A4_W, A4_H), Image.LANCZOS)
    pil_images.append(img)
    plt.close(fig)

pil_images[0].save(OUTPUT_PATH, save_all=True, append_images=pil_images[1:], resolution=150)
size_kb = os.path.getsize(OUTPUT_PATH) // 1024
print(f"\n✅ 保存完了: {OUTPUT_PATH}")
print(f"   ファイルサイズ: {size_kb} KB / {len(slides)} ページ")
