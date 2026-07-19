#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配当金収入 分析レポート v2 — Redesigned
出力: output/dividend_report_v2.pdf
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
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
plt.rcParams['font.size'] = 9

# ─── カラーパレット（洗練版） ─────────────────────────────────────────────────
BG      = '#F5F7FA'   # 背景
HDR     = '#1A2332'   # ヘッダー濃紺
ACCENT  = '#F5A623'   # ゴールド
C_JP    = '#2196F3'   # 日本株：青
C_US    = '#FF6B35'   # 米国株：オレンジ
C_BD    = '#9C27B0'   # 債券：紫
C_GRN   = '#43A047'   # 正
C_RED   = '#E53935'   # 負
C_GRAY  = '#6B7280'   # グレー
WHITE   = '#FFFFFF'
CARD    = '#FFFFFF'
BORDER  = '#DDE3ED'
TEXT    = '#1A2332'
TEXT2   = '#4A5568'

CAT_COLORS = {'日本株': C_JP, '米国株・ETF': C_US, '米国債利息': C_BD}

# ─── CSV 読み込み ─────────────────────────────────────────────────────────────
CSV_PATH = "/Users/takahiroazuma/Desktop/kabu/claude/data/DISTRIBUTION_20260627095220.csv"

with open(CSV_PATH, encoding='cp932', errors='replace') as f:
    raw_lines = f.readlines()

records = []
for line in raw_lines:
    line = line.strip()
    if not line: continue
    try: row = list(csv.reader([line]))[0]
    except: continue
    if len(row) < 6: continue
    if not re.match(r'^20\d\d/\d{1,2}/\d{1,2}$', row[0]): continue
    try:
        amt = float(row[5].replace(',', '').strip())
        records.append({
            'date': row[0], 'year': int(row[0][:4]),
            'month': int(row[0].split('/')[1]),
            'account': row[1], 'category': row[2],
            'name_raw': row[3], 'amount': amt,
        })
    except: continue

NAME_MAP = [
    ('ＮＴＴ',              'NTT'),
    ('日本電信電話',          'NTT'),
    ('ＫＤＤＩ',             'KDDI'),
    ('三井物産',              '三井物産'),
    ('蔵王産業',              '蔵王産業'),
    ('ジャックス',            'ジャックス'),
    ('オリックス',            'オリックス'),
    ('三菱ＵＦＪフィナンシャル', '三菱UFJ'),
    ('ジェイエイシーリクルートメント', 'JAC採用'),
    ('ＣＤＳ',               'CDS'),
    ('武田薬品工業',          '武田薬品'),
    ('三菱商事',              '三菱商事'),
    ('伊藤忠商事',            '伊藤忠'),
    ('バルカー',              'バルカー'),
    ('三井住友フィナンシャル', '三井住友FG'),
    ('東京海上ホールディングス', '東京海上'),
    ('第一生命ホールディングス', '第一生命'),
    ('第一ライフグループ',    '第一生命'),
    ('沖縄セルラー電話',      '沖縄セルラー'),
    ('三菱ＨＣキャピタル',    '三菱HC'),
    ('アサンテ',              'アサンテ'),
    ('アビスト',              'アビスト'),
    ('イー・ギャランティ',    'Eギャランティ'),
    ('信越化学工業',          '信越化学'),
    ('九州旅客鉄道',          'JR九州'),
    ('ソフトバンクグループ',  'SBG'),
    ('中国電力',              '中国電力'),
    ('バンガード トータルストックマーケット', 'VTI'),
    ('米国高配当株 ETF',      'HDV'),
    ('S&P500高配当株式ETF',   'SPYD'),
    ('S&P 500高配当株式ETF',  'SPYD'),
    ('メタ プラットフォームズ', 'META'),
    ('4.125',                 '米国債4.125%'),
    ('4.750',                 '米国債4.750%'),
    ('4.250',                 '米国債4.250%'),
    ('4.000',                 '米国債4.000%'),
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
print(f"読み込み: {len(df)}件  |  期間: {YEARS[0]}〜{YEARS[-1]}")
for y in YEARS:
    t = df[df['year']==y]['amount'].sum()
    print(f"  {y}年: {t/1e4:.1f}万円{'（部分）' if y in (2021,2026) else ''}")

# ─── 描画ヘルパー ─────────────────────────────────────────────────────────────

def new_fig():
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=BG)
    return fig

def draw_header(fig, title, subtitle="", accent=ACCENT):
    """上部ヘッダーバー"""
    ax = fig.add_axes([0, 0.895, 1, 0.105])
    ax.set_facecolor(HDR); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((0, 0), 1, 0.06, color=accent, transform=ax.transAxes))
    ax.text(0.022, 0.72, title, color=WHITE, fontsize=18,
            fontweight='bold', va='center', transform=ax.transAxes)
    if subtitle:
        ax.text(0.022, 0.26, subtitle, color='#94A3B8', fontsize=8.5,
                va='center', transform=ax.transAxes)

def draw_footer(fig, text, color=HDR):
    """下部フッター"""
    ax = fig.add_axes([0, 0, 1, 0.068])
    ax.set_facecolor(color); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.5, 0.5, text, ha='center', va='center', color=ACCENT,
            fontsize=9.5, fontweight='bold', transform=ax.transAxes)

def card(ax, x, y, w, h, title, value, sub="", color=C_JP, unit=""):
    """KPIカード"""
    r = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015",
                       lw=1.5, edgecolor=color, facecolor=CARD,
                       transform=ax.transAxes)
    ax.add_patch(r)
    # 左端のカラーバー
    bar = Rectangle((x, y), 0.006, h, color=color, transform=ax.transAxes)
    ax.add_patch(bar)
    tx = x + 0.016
    ax.text(tx, y + h*0.78, title, fontsize=8, color=TEXT2,
            va='center', transform=ax.transAxes)
    ax.text(tx, y + h*0.42, value + unit, fontsize=14, fontweight='bold',
            color=color, va='center', transform=ax.transAxes)
    if sub:
        ax.text(tx, y + h*0.14, sub, fontsize=7.5, color=C_GRAY,
                va='center', transform=ax.transAxes)

def draw_table(ax, headers, rows, x, y, col_widths, row_h=0.036,
               hdr_color=HDR, alt_color='#F0F4FA'):
    """クリーンなテーブル描画（重なりなし）"""
    n_cols = len(headers)
    # ヘッダー
    cx = x
    for h, w in zip(headers, col_widths):
        ax.add_patch(Rectangle((cx, y), w - 0.003, row_h * 1.15,
                               color=hdr_color, transform=ax.transAxes))
        ax.text(cx + w/2, y + row_h*0.575, h, ha='center', va='center',
                fontsize=8, fontweight='bold', color=WHITE, transform=ax.transAxes)
        cx += w
    # データ行
    for ri, row in enumerate(rows):
        ry  = y - (ri + 1) * row_h
        bg  = alt_color if ri % 2 == 0 else CARD
        cx  = x
        for j, (val, w) in enumerate(zip(row, col_widths)):
            ax.add_patch(Rectangle((cx, ry), w - 0.003, row_h,
                                   color=bg, transform=ax.transAxes))
            ax.add_patch(Rectangle((cx, ry), w - 0.003, row_h,
                                   fill=False, lw=0.4, edgecolor=BORDER,
                                   transform=ax.transAxes))
            style = val if isinstance(val, dict) else {'text': str(val), 'color': TEXT, 'bold': False}
            ax.text(cx + w/2, ry + row_h/2, style['text'],
                    ha='center', va='center', fontsize=8,
                    color=style.get('color', TEXT),
                    fontweight='bold' if style.get('bold') else 'normal',
                    transform=ax.transAxes)
            cx += w

def year_label(y):
    if y == 2021: return f"{y}\n(9月〜)"
    if y == 2026: return f"{y}\n(〜6/26)"
    return str(y)

def fmt_man(v):
    return f"{v/1e4:.1f}万" if v >= 1000 else f"{v:.0f}円"

# ════════════════════════════════════════════════════════════════════════════
# スライド 1: 表紙
# ════════════════════════════════════════════════════════════════════════════
def slide_cover():
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=HDR)
    ax  = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # 背景装飾
    for cx, cy, cr, ca in [(0.88, 0.85, 0.28, 0.04), (0.06, 0.12, 0.20, 0.03),
                            (0.50, 0.02, 0.40, 0.02)]:
        ax.add_patch(plt.Circle((cx, cy), cr, color='#2A3F5F', alpha=ca))
    ax.add_patch(Rectangle((0, 0.095), 1, 0.004, color=ACCENT, alpha=0.9))

    ax.text(0.5, 0.78, "配当金収入 分析レポート", ha='center', color=WHITE,
            fontsize=36, fontweight='bold')
    ax.text(0.5, 0.66, "SBI証券   2021年9月 〜 2026年6月26日", ha='center',
            color=ACCENT, fontsize=17, fontweight='bold')
    ax.text(0.5, 0.56, f"全 {len(df)} 件  ／  2026年は6月26日時点の最新データまで反映", ha='center',
            color='#94A3B8', fontsize=11)

    total      = df['amount'].sum()
    jp_total   = df[df['cat3']=='日本株']['amount'].sum()
    us_total   = df[df['cat3']=='米国株・ETF']['amount'].sum()
    bond_total = df[df['cat3']=='米国債利息']['amount'].sum()

    kpis = [
        ("累計配当合計（税後）", f"{total/1e4:.1f}万円",  "",              ACCENT),
        ("日本株 配当",          f"{jp_total/1e4:.1f}万円", "特定・NISA",   C_JP),
        ("米国株・ETF",          f"{us_total/1e4:.1f}万円", "HDV/VTI/SPYD等", C_US),
        ("米国債 利息",          f"{bond_total/1e4:.1f}万円", "4本保有中",   C_BD),
    ]
    for i, (lbl, val, sub, clr) in enumerate(kpis):
        bx = 0.06 + i * 0.225
        r = FancyBboxPatch((bx, 0.20), 0.205, 0.22,
                           boxstyle="round,pad=0.015", lw=2,
                           edgecolor=clr, facecolor='#0D1520',
                           transform=ax.transAxes)
        ax.add_patch(r)
        ax.add_patch(Rectangle((bx, 0.20), 0.007, 0.22, color=clr,
                               transform=ax.transAxes))
        ax.text(bx+0.018, 0.386, lbl, color='#94A3B8', fontsize=8.5,
                transform=ax.transAxes)
        ax.text(bx+0.018, 0.318, val, color=clr, fontsize=14,
                fontweight='bold', transform=ax.transAxes)
        if sub:
            ax.text(bx+0.018, 0.245, sub, color='#4A5568', fontsize=8,
                    transform=ax.transAxes)

    ax.text(0.5, 0.12, "※ 2021年は9月から・2026年は6月26日までの部分データです",
            ha='center', color='#4A5568', fontsize=9)
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 2: 年別配当推移と合計
# ════════════════════════════════════════════════════════════════════════════
def slide_annual():
    by_yc = df.groupby(['year','cat3'])['amount'].sum().unstack(fill_value=0)
    for c in ['日本株','米国株・ETF','米国債利息']:
        if c not in by_yc.columns: by_yc[c] = 0
    total_by_year = df.groupby('year')['amount'].sum()
    full_years = [y for y in YEARS if y not in (2021, 2026)]
    avg_full   = np.mean([total_by_year.get(y, 0) for y in full_years])
    growth     = (total_by_year.get(2025,0)/total_by_year.get(2022,0)-1)*100

    fig = new_fig()
    draw_header(fig, "年別 配当金 推移と合計",
                f"累計合計: {df['amount'].sum()/1e4:.1f}万円（税引後）  ｜  ※2021年:9月〜 / 2026年:〜6/26 は部分データ")

    ax = fig.add_axes([0, 0.07, 1, 0.82]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # KPIカード 4枚（上段）
    card_data = [
        ("2025年（最高）", f"{total_by_year.get(2025,0)/1e4:.1f}万円",
         "過去最高額", ACCENT),
        ("2024年",        f"{total_by_year.get(2024,0)/1e4:.1f}万円",
         f"前年比 +{(total_by_year.get(2024,0)/total_by_year.get(2023,0)-1)*100:.0f}%", C_JP),
        ("年平均 (2022-25)", f"{avg_full/1e4:.1f}万円",
         "通年ベース", C_US),
        ("2022→2025 成長",  f"+{growth:.0f}%",
         "3年間の増加率", C_GRN),
    ]
    for i, (lbl, val, sub, clr) in enumerate(card_data):
        card(ax, 0.02+i*0.243, 0.82, 0.232, 0.12, lbl, val, sub, clr)

    # 左: 積み上げ棒グラフ
    ax1 = fig.add_axes([0.04, 0.25, 0.54, 0.52])
    xs = np.arange(len(YEARS))
    bottoms = np.zeros(len(YEARS))
    cats = ['日本株','米国株・ETF','米国債利息']
    for cat in cats:
        vals = [by_yc.loc[y, cat] if y in by_yc.index else 0 for y in YEARS]
        ax1.bar(xs, [v/1e4 for v in vals], 0.58, bottom=[b/1e4 for b in bottoms],
                color=CAT_COLORS[cat], edgecolor=BG, linewidth=1.2, label=cat)
        bottoms += np.array(vals)
    # 合計ラベル（バーの上に1つだけ）
    max_val = total_by_year.max()
    for i, y in enumerate(YEARS):
        tot = total_by_year.get(y, 0)
        ax1.text(i, tot/1e4 + max_val/1e4*0.015, f'{tot/1e4:.1f}万',
                 ha='center', fontsize=9, fontweight='bold', color=TEXT)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([year_label(y) for y in YEARS], fontsize=9.5)
    ax1.set_ylabel('配当金（万円）', fontsize=9.5, color=TEXT2)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.set_title('年別 カテゴリ別 配当合計', fontsize=12, fontweight='bold',
                  color=TEXT, pad=10)
    ax1.legend(fontsize=9, loc='upper left', framealpha=0.9,
               edgecolor=BORDER, fancybox=True)
    ax1.set_facecolor(BG)
    ax1.grid(axis='y', color=BORDER, linewidth=0.8, alpha=0.7)
    ax1.spines[['top','right','left','bottom']].set_color(BORDER)
    ax1.tick_params(colors=TEXT2)

    # 右: 合計テーブル（年×カテゴリ）
    ax2 = fig.add_axes([0.61, 0.12, 0.37, 0.65])
    ax2.axis('off'); ax2.set_xlim(0,1); ax2.set_ylim(0,1)

    ax2.text(0.5, 0.97, "年別・カテゴリ別 配当一覧（万円）", ha='center',
             fontsize=10, fontweight='bold', color=TEXT, transform=ax2.transAxes)

    col_ws2 = [0.25, 0.22, 0.22, 0.22, 0.09]
    hdrs2   = ['年', '日本株', '米国株・ETF', '米国債利息', '合計']
    hdr_row_h = 0.075
    data_row_h = 0.083

    # ヘッダー
    cx2 = 0.0
    hdr_y = 0.88
    for h, w2 in zip(hdrs2, col_ws2):
        ax2.add_patch(Rectangle((cx2, hdr_y), w2-0.01, hdr_row_h,
                                color=HDR, transform=ax2.transAxes))
        ax2.text(cx2+w2/2, hdr_y+hdr_row_h/2, h, ha='center', va='center',
                 fontsize=9, fontweight='bold', color=WHITE, transform=ax2.transAxes)
        cx2 += w2

    # データ行
    all_rows = [(y, y in (2021,2026)) for y in YEARS]
    for ri, (y, is_partial) in enumerate(all_rows):
        ry2 = hdr_y - (ri+1)*data_row_h
        bg2 = '#F0F4FA' if ri%2==0 else CARD
        jp_v  = by_yc.loc[y,'日本株'] if y in by_yc.index else 0
        us_v  = by_yc.loc[y,'米国株・ETF'] if y in by_yc.index else 0
        bd_v  = by_yc.loc[y,'米国債利息'] if y in by_yc.index else 0
        tot_v = jp_v + us_v + bd_v
        tag   = '※' if is_partial else ''
        row_vals = [f"{y}年{tag}",
                    f"{jp_v/1e4:.1f}",
                    f"{us_v/1e4:.1f}",
                    f"{bd_v/1e4:.1f}",
                    f"{tot_v/1e4:.1f}"]
        cx2 = 0.0
        for j, (val, w2) in enumerate(zip(row_vals, col_ws2)):
            ax2.add_patch(Rectangle((cx2, ry2), w2-0.01, data_row_h,
                                    color=bg2, transform=ax2.transAxes))
            ax2.add_patch(Rectangle((cx2, ry2), w2-0.01, data_row_h,
                                    fill=False, lw=0.5, edgecolor=BORDER,
                                    transform=ax2.transAxes))
            clr2 = (C_JP if j==1 else C_US if j==2 else C_BD if j==3 else
                    ACCENT if j==4 else TEXT)
            fw2  = 'bold' if j in (0, 4) else 'normal'
            ax2.text(cx2+w2/2, ry2+data_row_h/2, val, ha='center', va='center',
                     fontsize=9, color=clr2, fontweight=fw2,
                     transform=ax2.transAxes)
            cx2 += w2

    # ※説明
    note_y = hdr_y - len(all_rows)*data_row_h - 0.06
    ax2.text(0.02, note_y, "※ 2021年=9月〜、2026年=〜6/26の部分データ",
             fontsize=8, color=C_GRAY, transform=ax2.transAxes)

    draw_footer(fig, f"2025年 {total_by_year.get(2025,0)/1e4:.1f}万円が過去最高。"
                f"2022年比 +{growth:.0f}%の増加。2026年は{total_by_year.get(2026,0)/1e4:.1f}万円受取済み（6月26日時点）。")
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 3: 月別受取パターン
# ════════════════════════════════════════════════════════════════════════════
def slide_monthly():
    MONTHS_JP = ['1月','2月','3月','4月','5月','6月',
                 '7月','8月','9月','10月','11月','12月']

    fig = new_fig()
    draw_header(fig, "月別 配当受取パターン",
                "6月・12月に日本株が集中。3・6・9・12月に米国ETFが四半期入金。5・11月に米国債利息。")

    ax = fig.add_axes([0, 0.07, 1, 0.82]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # 上段: 全期間 月別積み上げ棒グラフ（大きめ）
    ax1 = fig.add_axes([0.05, 0.42, 0.55, 0.47])
    xs = np.arange(12)
    bottoms = np.zeros(12)
    for cat in ['日本株','米国株・ETF','米国債利息']:
        sub = df[df['cat3']==cat]
        vals = [sub[sub['month']==m]['amount'].sum() for m in range(1,13)]
        ax1.bar(xs, [v/1e4 for v in vals], 0.65, bottom=[b/1e4 for b in bottoms],
                color=CAT_COLORS[cat], edgecolor=BG, linewidth=1, label=cat)
        bottoms += np.array(vals)
    # 合計ラベルは6月と12月のみ（主要月だけ表示して重ならないように）
    for i in range(12):
        tot = df[df['month']==i+1]['amount'].sum()
        if tot > 0 and i+1 in [3, 6, 9, 11, 12]:
            ax1.text(i, tot/1e4 + 0.4, f'{tot/1e4:.1f}万', ha='center',
                     fontsize=8.5, fontweight='bold', color=TEXT)
    ax1.set_xticks(xs)
    ax1.set_xticklabels(MONTHS_JP, fontsize=10)
    ax1.set_ylabel('累計配当（万円）', fontsize=10, color=TEXT2)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.set_title('月別 累計配当（全期間 / カテゴリ別積み上げ）',
                  fontsize=12, fontweight='bold', color=TEXT, pad=10)
    ax1.legend(fontsize=9.5, loc='upper right', framealpha=0.9,
               edgecolor=BORDER, fancybox=True)
    ax1.set_facecolor(BG)
    ax1.grid(axis='y', color=BORDER, linewidth=0.8, alpha=0.7)
    ax1.spines[['top','right','left','bottom']].set_color(BORDER)
    ax1.tick_params(colors=TEXT2)

    # 右上: 2025年 月別内訳
    ax2 = fig.add_axes([0.64, 0.42, 0.33, 0.47])
    df25 = df[df['year']==2025]
    bottoms2 = np.zeros(12)
    for cat in ['日本株','米国株・ETF','米国債利息']:
        sub2 = df25[df25['cat3']==cat]
        vals2 = [sub2[sub2['month']==m]['amount'].sum() for m in range(1,13)]
        ax2.bar(xs, [v/1e4 for v in vals2], 0.65, bottom=[b/1e4 for b in bottoms2],
                color=CAT_COLORS[cat], edgecolor=BG, linewidth=1, label=cat)
        bottoms2 += np.array(vals2)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([m[:2] for m in MONTHS_JP], fontsize=9)
    ax2.set_ylabel('万円', fontsize=9.5, color=TEXT2)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax2.set_title('2025年 月別内訳', fontsize=11, fontweight='bold', color=TEXT, pad=10)
    ax2.set_facecolor(BG)
    ax2.grid(axis='y', color=BORDER, linewidth=0.8, alpha=0.7)
    ax2.spines[['top','right','left','bottom']].set_color(BORDER)
    ax2.tick_params(colors=TEXT2)

    # 下段: 主要月の年別一覧テーブル
    ax.text(0.03, 0.375, "主要入金月 × 年別 配当合計（万円）",
            fontsize=10, fontweight='bold', color=TEXT, transform=ax.transAxes)

    key_months = [3, 5, 6, 9, 11, 12]
    col_ws3 = [0.085] + [0.098]*len(YEARS) + [0.085, 0.070]
    hdrs3   = ['月'] + [year_label(y).replace('\n','') for y in YEARS] + ['合計', '比率']

    # ヘッダー
    cx3 = 0.03
    hy3 = 0.335
    rh3 = 0.043
    for h, w3 in zip(hdrs3, col_ws3):
        ax.add_patch(Rectangle((cx3, hy3), w3-0.004, rh3,
                               color=HDR, transform=ax.transAxes))
        ax.text(cx3+w3/2, hy3+rh3/2, h, ha='center', va='center',
                fontsize=8, fontweight='bold', color=WHITE, transform=ax.transAxes)
        cx3 += w3

    total_all = df['amount'].sum()
    for ri, m in enumerate(key_months):
        ry3 = hy3 - (ri+1)*rh3
        bg3 = '#EEF4FF' if m in (6,12) else ('#FFF4EE' if m in (3,9) else '#F0F4FA')
        m_total = df[df['month']==m]['amount'].sum()
        pct     = m_total / total_all * 100
        m_clr   = C_JP if m in (6,12) else (C_US if m in (3,9) else C_BD)
        y_vals  = [df[(df['year']==y)&(df['month']==m)]['amount'].sum() for y in YEARS]
        row_v   = ([f"{m}月"] + [f'{v/1e4:.1f}' if v>0 else '—' for v in y_vals] +
                   [f'{m_total/1e4:.1f}万', f'{pct:.1f}%'])
        cx3 = 0.03
        for j, (val, w3) in enumerate(zip(row_v, col_ws3)):
            ax.add_patch(Rectangle((cx3, ry3), w3-0.004, rh3,
                                   color=bg3, transform=ax.transAxes))
            ax.add_patch(Rectangle((cx3, ry3), w3-0.004, rh3,
                                   fill=False, lw=0.4, edgecolor=BORDER,
                                   transform=ax.transAxes))
            fc3 = m_clr if j==0 else (TEXT if j < len(YEARS)+1 else ACCENT)
            fw3 = 'bold' if j == 0 or j >= len(YEARS)+1 else 'normal'
            ax.text(cx3+w3/2, ry3+rh3/2, val, ha='center', va='center',
                    fontsize=8.5, color=fc3, fontweight=fw3, transform=ax.transAxes)
            cx3 += w3

    draw_footer(fig,
                "6月・12月: 日本株 決算配当（年2回）  ｜  "
                "3・6・9・12月: 米国ETF 四半期配当  ｜  5・11月: 米国債 半期利息")
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 4: 日本株 銘柄別推移
# ════════════════════════════════════════════════════════════════════════════
def slide_jp():
    jp    = df[df['cat3']=='日本株']
    by_ny = jp.groupby(['name','year'])['amount'].sum().unstack(fill_value=0)
    for y in YEARS:
        if y not in by_ny.columns: by_ny[y] = 0
    by_ny   = by_ny[sorted(by_ny.columns)]
    totals  = by_ny.sum(axis=1).sort_values(ascending=False)
    top9    = totals.head(9).index.tolist()

    fig = new_fig()
    draw_header(fig, "日本株 銘柄別・年別 配当推移",
                f"日本株 累計: {jp['amount'].sum()/1e4:.1f}万円（税引後）  ｜  上位9銘柄を表示")

    ax = fig.add_axes([0, 0.07, 1, 0.82]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # 左: グループ棒グラフ（上位5銘柄、見やすく）
    top5   = top9[:5]
    clrs5  = [C_JP, '#42A5F5', C_GRN, C_US, ACCENT]
    ax1 = fig.add_axes([0.03, 0.32, 0.46, 0.55])
    n_y = len(YEARS); gw = 0.75; bw = gw / len(top5)
    for ti, (name, clr) in enumerate(zip(top5, clrs5)):
        offs = np.arange(n_y) - gw/2 + (ti+0.5)*bw
        vals = [by_ny.loc[name, y] if name in by_ny.index else 0 for y in YEARS]
        ax1.bar(offs, [v/1e4 for v in vals], bw*0.85,
                color=clr, edgecolor=BG, linewidth=0.8, label=name)
    ax1.set_xticks(np.arange(n_y))
    ax1.set_xticklabels([year_label(y) for y in YEARS], fontsize=9.5)
    ax1.set_ylabel('配当（万円）', fontsize=10, color=TEXT2)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.set_title('上位5銘柄 年別配当比較', fontsize=12, fontweight='bold',
                  color=TEXT, pad=10)
    ax1.legend(fontsize=9, ncol=3, loc='upper left',
               framealpha=0.9, edgecolor=BORDER, fancybox=True)
    ax1.set_facecolor(BG)
    ax1.grid(axis='y', color=BORDER, linewidth=0.8, alpha=0.7)
    ax1.spines[['top','right','left','bottom']].set_color(BORDER)
    ax1.tick_params(colors=TEXT2)

    # 右: 折れ線（上位4銘柄トレンド）
    ax2 = fig.add_axes([0.54, 0.32, 0.43, 0.55])
    line_clrs = [C_JP, C_GRN, C_US, C_BD]
    for name, clr in zip(top9[:4], line_clrs):
        vals = [by_ny.loc[name, y] if name in by_ny.index else 0 for y in YEARS]
        ax2.plot(YEARS, [v/1e4 for v in vals], 'o-', color=clr,
                 lw=2.2, ms=7, label=name, zorder=3)
        ax2.annotate(f'{vals[-1]/1e4:.1f}万',
                     xy=(YEARS[-1], vals[-1]/1e4),
                     xytext=(6, 0), textcoords='offset points',
                     fontsize=8.5, color=clr, fontweight='bold', va='center')
    ax2.set_xticks(YEARS)
    ax2.set_xticklabels([str(y) for y in YEARS], fontsize=9, rotation=30, ha='right')
    ax2.set_ylabel('万円', fontsize=10, color=TEXT2)
    ax2.set_title('上位4銘柄 年次推移', fontsize=12, fontweight='bold',
                  color=TEXT, pad=10)
    ax2.legend(fontsize=9, framealpha=0.9, edgecolor=BORDER, fancybox=True)
    ax2.set_facecolor(BG)
    ax2.grid(color=BORDER, linewidth=0.8, alpha=0.7)
    ax2.spines[['top','right','left','bottom']].set_color(BORDER)
    ax2.tick_params(colors=TEXT2)

    # 下: ランキングテーブル（9銘柄）
    ax.text(0.03, 0.298, "銘柄別 年間配当一覧（万円・税引後）",
            fontsize=10, fontweight='bold', color=TEXT, transform=ax.transAxes)
    col_ws_t = [0.115, 0.075] + [0.085]*len(YEARS) + [0.075, 0.075]
    hdrs_t   = ['銘柄', '累計'] + [year_label(y).replace('\n','') for y in YEARS] + ['前年比', '傾向']

    cx_t = 0.03; hy_t = 0.258; rh_t = 0.033
    for h, w in zip(hdrs_t, col_ws_t):
        ax.add_patch(Rectangle((cx_t, hy_t), w-0.003, rh_t+0.004,
                               color=HDR, transform=ax.transAxes))
        ax.text(cx_t+w/2, hy_t+(rh_t+0.004)/2, h, ha='center', va='center',
                fontsize=8, fontweight='bold', color=WHITE, transform=ax.transAxes)
        cx_t += w

    for ri, name in enumerate(top9):
        ry_t = hy_t - (ri+1)*rh_t
        bg_t = '#F0F4FA' if ri%2==0 else CARD
        cum  = totals[name]
        v24  = by_ny.loc[name, 2024] if (name in by_ny.index and 2024 in by_ny.columns) else 0
        v25  = by_ny.loc[name, 2025] if (name in by_ny.index and 2025 in by_ny.columns) else 0
        yoy  = f'{(v25/v24-1)*100:+.0f}%' if v24>0 else '—'
        trend, tc = (('↑', C_GRN) if v25>v24*1.05 else ('↓', C_RED) if v25<v24*0.95 else ('→', C_GRAY))
        row_v = ([name, f'{cum/1e4:.1f}万'] +
                 [f'{by_ny.loc[name,y]/1e4:.1f}' if (name in by_ny.index and y in by_ny.columns) else '—'
                  for y in YEARS] + [yoy, trend])
        cx_t = 0.03
        for j, (val, w) in enumerate(zip(row_v, col_ws_t)):
            ax.add_patch(Rectangle((cx_t, ry_t), w-0.003, rh_t,
                                   color=bg_t, transform=ax.transAxes))
            ax.add_patch(Rectangle((cx_t, ry_t), w-0.003, rh_t,
                                   fill=False, lw=0.4, edgecolor=BORDER,
                                   transform=ax.transAxes))
            n_years = len(YEARS)
            if j == 0:   fc_t, fw_t = C_JP,  'bold'
            elif j == 1: fc_t, fw_t = ACCENT, 'bold'
            elif j == n_years+2: fc_t, fw_t = (C_GRN if '+' in yoy else C_RED if '-' in yoy else C_GRAY), 'bold'
            elif j == n_years+3: fc_t, fw_t = tc, 'bold'
            else:        fc_t, fw_t = TEXT,  'normal'
            ax.text(cx_t+w/2, ry_t+rh_t/2, val, ha='center', va='center',
                    fontsize=8.5, color=fc_t, fontweight=fw_t, transform=ax.transAxes)
            cx_t += w

    jp25 = jp[jp['year']==2025]['amount'].sum()
    jp24 = jp[jp['year']==2024]['amount'].sum()
    draw_footer(fig,
                f"2025年 日本株配当: {jp25/1e4:.1f}万円（前年比 {(jp25/jp24-1)*100:+.0f}%）。"
                "蔵王産業・JAC採用・三井物産が累計上位3銘柄。")
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 5: 米国株・ETF・米国債
# ════════════════════════════════════════════════════════════════════════════
def slide_us():
    us    = df[df['cat3'] != '日本株']
    by_ny = us.groupby(['name','year'])['amount'].sum().unstack(fill_value=0)
    for y in YEARS:
        if y not in by_ny.columns: by_ny[y] = 0
    by_ny     = by_ny[sorted(by_ny.columns)]
    totals_us = by_ny.sum(axis=1).sort_values(ascending=False)

    etf_names  = [n for n in ['HDV','VTI','SPYD','META'] if n in by_ny.index]
    bond_names = [n for n in by_ny.index if '米国債' in n]
    etf_clrs   = {'HDV': C_US, 'VTI': C_JP, 'SPYD': C_GRN, 'META': C_BD}
    bond_clrs  = [C_BD, '#7B1FA2', '#AB47BC', '#CE93D8']

    fig = new_fig()
    draw_header(fig, "米国株・ETF・米国債 銘柄別配当推移",
                f"米国株・ETF 累計: {df[df['cat3']=='米国株・ETF']['amount'].sum()/1e4:.1f}万円  ｜  "
                f"米国債利息 累計: {df[df['cat3']=='米国債利息']['amount'].sum()/1e4:.1f}万円（税引後）",
                accent=C_US)

    ax = fig.add_axes([0, 0.07, 1, 0.82]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # 左上: ETF年別グループ棒グラフ
    ax1 = fig.add_axes([0.04, 0.46, 0.44, 0.43])
    n_y = len(YEARS); gw = 0.75; bw = gw / max(len(etf_names), 1)
    for ti, name in enumerate(etf_names):
        offs = np.arange(n_y) - gw/2 + (ti+0.5)*bw
        vals = [by_ny.loc[name, y] for y in YEARS]
        ax1.bar(offs, [v/1e4 for v in vals], bw*0.85,
                color=etf_clrs.get(name, C_GRAY),
                edgecolor=BG, label=name, linewidth=0.8)
    ax1.set_xticks(np.arange(n_y))
    ax1.set_xticklabels([year_label(y) for y in YEARS], fontsize=9)
    ax1.set_ylabel('万円', fontsize=9.5, color=TEXT2)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax1.set_title('米国ETF・株 年別配当', fontsize=11, fontweight='bold', color=TEXT, pad=8)
    ax1.legend(fontsize=9, loc='upper left', framealpha=0.9, edgecolor=BORDER)
    ax1.set_facecolor(BG)
    ax1.grid(axis='y', color=BORDER, linewidth=0.8, alpha=0.7)
    ax1.spines[['top','right','left','bottom']].set_color(BORDER)
    ax1.tick_params(colors=TEXT2)

    # 右上: 米国債 年別棒グラフ
    ax2 = fig.add_axes([0.54, 0.46, 0.43, 0.43])
    bw2 = 0.7 / max(len(bond_names), 1)
    for bi, (name, clr) in enumerate(zip(bond_names, bond_clrs)):
        offs2 = np.arange(n_y) - 0.35 + (bi+0.5)*bw2
        vals2 = [by_ny.loc[name, y] for y in YEARS]
        ax2.bar(offs2, [v/1e4 for v in vals2], bw2*0.85,
                color=clr, edgecolor=BG, label=name, linewidth=0.8)
    ax2.set_xticks(np.arange(n_y))
    ax2.set_xticklabels([year_label(y) for y in YEARS], fontsize=9)
    ax2.set_ylabel('万円', fontsize=9.5, color=TEXT2)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}万'))
    ax2.set_title('米国債 年別利息収入', fontsize=11, fontweight='bold', color=TEXT, pad=8)
    ax2.legend(fontsize=8.5, framealpha=0.9, edgecolor=BORDER)
    ax2.set_facecolor(BG)
    ax2.grid(axis='y', color=BORDER, linewidth=0.8, alpha=0.7)
    ax2.spines[['top','right','left','bottom']].set_color(BORDER)
    ax2.tick_params(colors=TEXT2)

    # 下: テーブル（全米国銘柄）
    ax.text(0.03, 0.42, "銘柄別 年間配当一覧（万円・税引後）",
            fontsize=10, fontweight='bold', color=TEXT, transform=ax.transAxes)

    all_us_names = totals_us.index.tolist()
    n_rows = len(all_us_names)
    col_ws_u = [0.155, 0.075] + [0.085]*len(YEARS) + [0.075, 0.075]
    hdrs_u   = ['銘柄', '累計'] + [year_label(y).replace('\n','') for y in YEARS] + ['前年比', '傾向']

    cx_u = 0.03; hy_u = 0.385; rh_u = min(0.036, 0.32/max(n_rows,1))
    for h, w in zip(hdrs_u, col_ws_u):
        ax.add_patch(Rectangle((cx_u, hy_u), w-0.003, rh_u+0.004,
                               color=HDR, transform=ax.transAxes))
        ax.text(cx_u+w/2, hy_u+(rh_u+0.004)/2, h, ha='center', va='center',
                fontsize=8, fontweight='bold', color=WHITE, transform=ax.transAxes)
        cx_u += w

    for ri, name in enumerate(all_us_names):
        ry_u = hy_u - (ri+1)*rh_u
        bg_u = '#F3EEFF' if ri%2==0 else CARD
        cum  = totals_us[name]
        v24  = by_ny.loc[name,2024] if 2024 in by_ny.columns else 0
        v25  = by_ny.loc[name,2025] if 2025 in by_ny.columns else 0
        yoy  = f'{(v25/v24-1)*100:+.0f}%' if v24>0 else '—'
        trend, tc = (('↑', C_GRN) if v25>v24*1.05 else ('↓', C_RED) if v25<v24*0.95 else ('→', C_GRAY))
        row_v = ([name, f'{cum/1e4:.1f}万'] +
                 [f'{by_ny.loc[name,y]/1e4:.1f}' if y in by_ny.columns else '—'
                  for y in YEARS] + [yoy, trend])
        cx_u = 0.03
        for j, (val, w) in enumerate(zip(row_v, col_ws_u)):
            ax.add_patch(Rectangle((cx_u, ry_u), w-0.003, rh_u,
                                   color=bg_u, transform=ax.transAxes))
            ax.add_patch(Rectangle((cx_u, ry_u), w-0.003, rh_u,
                                   fill=False, lw=0.4, edgecolor=BORDER,
                                   transform=ax.transAxes))
            n_yr = len(YEARS)
            if j==0:       fc_u, fw_u = C_BD,  'bold'
            elif j==1:     fc_u, fw_u = ACCENT, 'bold'
            elif j==n_yr+2: fc_u, fw_u = (C_GRN if '+' in yoy else C_RED if '-' in yoy else C_GRAY), 'bold'
            elif j==n_yr+3: fc_u, fw_u = tc, 'bold'
            else:          fc_u, fw_u = TEXT,  'normal'
            ax.text(cx_u+w/2, ry_u+rh_u/2, val, ha='center', va='center',
                    fontsize=8.5, color=fc_u, fontweight=fw_u, transform=ax.transAxes)
            cx_u += w

    hdv25 = df[(df['name']=='HDV')&(df['year']==2025)]['amount'].sum()
    hdv24 = df[(df['name']=='HDV')&(df['year']==2024)]['amount'].sum()
    draw_footer(fig,
                f"HDV 2025年: {hdv25/1e4:.1f}万円（前年比 {(hdv25/hdv24-1)*100:+.0f}%）。"
                "NISA枠88株追加で非課税分が増加。米国債4.250%は2025年6月に満期・償還済み。",
                color='#4A1070')
    return fig

# ════════════════════════════════════════════════════════════════════════════
# スライド 6: 全銘柄累計ランキング
# ════════════════════════════════════════════════════════════════════════════
def slide_ranking():
    by_name   = df.groupby('name')['amount'].sum().sort_values(ascending=False)
    by_year   = df.groupby('year')['amount'].sum()
    full_years = [y for y in YEARS if y not in (2021, 2026)]

    fig = new_fig()
    draw_header(fig, "全銘柄 累計配当ランキング",
                f"全{len(by_name)}銘柄  ｜  累計総額: {df['amount'].sum()/1e4:.1f}万円（税引後）  ｜  上位20銘柄を表示")

    ax = fig.add_axes([0, 0.07, 1, 0.82]); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # 左: 水平棒グラフ（上位20）
    ax1 = fig.add_axes([0.03, 0.09, 0.50, 0.79])
    names20 = by_name.index[:20].tolist()
    vals20  = [by_name[n] for n in names20]
    cat_clr_map = {}
    for n in names20:
        m = df[df['name']==n]['cat3'].mode()
        cat_clr_map[n] = (C_JP if len(m)>0 and m[0]=='日本株' else
                          C_US if len(m)>0 and m[0]=='米国株・ETF' else C_BD)
    bar_colors_r = [cat_clr_map[n] for n in names20]
    bars = ax1.barh(range(len(names20)), [v/1e4 for v in vals20],
                    color=bar_colors_r, edgecolor=BG, height=0.72, linewidth=0.8)
    ax1.set_yticks(range(len(names20)))
    ax1.set_yticklabels(names20, fontsize=9.5)
    ax1.invert_yaxis()
    ax1.set_xlabel('累計配当（万円）', fontsize=9.5, color=TEXT2)
    ax1.set_title('全銘柄 累計配当ランキング（上位20）',
                  fontsize=12, fontweight='bold', color=TEXT, pad=10)
    ax1.set_facecolor(BG)
    ax1.grid(axis='x', color=BORDER, linewidth=0.8, alpha=0.7)
    ax1.spines[['top','right','left','bottom']].set_color(BORDER)
    ax1.tick_params(colors=TEXT2)
    max_v = max(vals20)/1e4
    for bar, val in zip(bars, vals20):
        ax1.text(bar.get_width() + max_v*0.012,
                 bar.get_y() + bar.get_height()/2,
                 f'{val/1e4:.1f}万', va='center', fontsize=9, fontweight='bold', color=TEXT)
    ax1.set_xlim(0, max_v * 1.20)
    patches_leg = [mpatches.Patch(color=C_JP,  label='日本株'),
                   mpatches.Patch(color=C_US,  label='米国株・ETF'),
                   mpatches.Patch(color=C_BD,  label='米国債利息')]
    ax1.legend(handles=patches_leg, fontsize=9.5, loc='lower right',
               framealpha=0.9, edgecolor=BORDER, fancybox=True)

    # 右上: 年別合計棒グラフ（通年のみ）
    ax2 = fig.add_axes([0.58, 0.52, 0.39, 0.36])
    fy_vals = [by_year.get(y,0)/1e4 for y in full_years]
    bar_clrs2 = [ACCENT if v==max(fy_vals) else C_JP for v in fy_vals]
    bars2 = ax2.bar(range(len(full_years)), fy_vals, color=bar_clrs2,
                    edgecolor=BG, linewidth=1, width=0.6)
    ax2.set_xticks(range(len(full_years)))
    ax2.set_xticklabels([str(y) for y in full_years], fontsize=10.5)
    ax2.set_ylabel('万円', fontsize=9.5, color=TEXT2)
    ax2.set_title('通年ベース 年別合計', fontsize=11, fontweight='bold', color=TEXT, pad=8)
    ax2.set_facecolor(BG)
    ax2.grid(axis='y', color=BORDER, linewidth=0.8, alpha=0.7)
    ax2.spines[['top','right','left','bottom']].set_color(BORDER)
    ax2.tick_params(colors=TEXT2)
    for bar, val in zip(bars2, fy_vals):
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.4,
                 f'{val:.1f}万', ha='center', fontsize=10, fontweight='bold', color=TEXT)

    # 右下: 展望インサイトカード（4枚）
    ax.text(0.59, 0.475, "今後の展望・ポイント",
            fontsize=11, fontweight='bold', color=TEXT, transform=ax.transAxes)
    insights = [
        (C_JP,  "安定増配トレンド",
         "三井物産・三菱UFJ等は連続増配。\n蔵王産業も高水準を維持継続。"),
        (C_US,  "HDV NISA追加の効果",
         "NISA枠88株追加で非課税配当が増加。\nNISA優先での保有拡充が有効。"),
        (C_BD,  "米国債4.250%満期済み",
         "2025年6月に償還完了。3銘柄体制へ。\n年間利息は約15万円ペース。"),
        (ACCENT,"2026年の受取ペース",
         f"6月26日時点で{by_year.get(2026,0)/1e4:.1f}万円受取済み。\n年換算で約{by_year.get(2026,0)/6*12/1e4:.0f}万円ペース。"),
    ]
    for i, (clr, title, desc) in enumerate(insights):
        iy = 0.415 - i * 0.108
        r = FancyBboxPatch((0.59, iy), 0.395, 0.095,
                           boxstyle="round,pad=0.012", lw=1.5,
                           edgecolor=clr, facecolor=CARD,
                           transform=ax.transAxes)
        ax.add_patch(r)
        ax.add_patch(Rectangle((0.59, iy), 0.006, 0.095, color=clr,
                               transform=ax.transAxes))
        ax.text(0.603, iy+0.065, f"● {title}", fontsize=9.5,
                fontweight='bold', color=clr, transform=ax.transAxes)
        ax.text(0.603, iy+0.020, desc, fontsize=8.5, color=TEXT2,
                transform=ax.transAxes)

    y25 = by_year.get(2025,0); y22 = by_year.get(2022,0)
    draw_footer(fig,
                f"累計 {df['amount'].sum()/1e4:.1f}万円。2025年: {y25/1e4:.1f}万（2022年比 +{(y25/y22-1)*100:.0f}%）。"
                f"2026年は6/26時点で {by_year.get(2026,0)/1e4:.1f}万円、年換算 約{by_year.get(2026,0)/6*12/1e4:.0f}万円ペース。")
    return fig

# ─── PDF 出力 ─────────────────────────────────────────────────────────────────
OUTPUT_DIR  = "/Users/takahiroazuma/Desktop/kabu/claude/output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dividend_report_v2.pdf")
os.makedirs(OUTPUT_DIR, exist_ok=True)

slides = [slide_cover, slide_annual, slide_monthly,
          slide_jp, slide_us, slide_ranking]

A4_W = int(297 * 150 / 25.4)
A4_H = int(210 * 150 / 25.4)

print("\nPDF 生成中...")
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
print(f"   {size_kb} KB / {len(slides)} ページ")
