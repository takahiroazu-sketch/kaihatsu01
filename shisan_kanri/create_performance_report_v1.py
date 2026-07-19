#!/usr/bin/env python3
"""個別株パフォーマンス分析レポート v1 - 資産額推移・配当成長の総合評価"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.gridspec import GridSpec
import numpy as np, os, re
from collections import defaultdict
from io import BytesIO
from PIL import Image

# ── フォント ──────────────────────────────────────────────
import matplotlib.font_manager as fm
_CANDIDATES = [
    '/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
    '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
    '/Library/Fonts/Hiragino Sans GB.ttc',
]
_jp_font_path = next((c for c in _CANDIDATES if os.path.exists(c)), None)
def jf(size=10, bold=False):
    fp = fm.FontProperties(fname=_jp_font_path) if _jp_font_path else fm.FontProperties()
    fp.set_size(size); fp.set_weight('bold' if bold else 'normal'); return fp
plt.rcParams['axes.unicode_minus'] = False

# ── デザイントークン (v4 approved) ─────────────────────────
BG='#EDEAE6'; TEXT='#1A1A1A'; TEXT2='#6B6560'; TEAL='#00B4CC'
BLUE1='#5BAED0'; BLUE2='#8EC8E8'; AMBER='#D4820C'; PURPLE='#8870CC'
POS='#2D8A50'; NEG='#C03030'; FOOTER='#1C1C1C'; WHITE='#FFFFFF'
HDRBG='#D4D0CC'; ALTBG='#F5F2EE'; BORDER='#C8C4BE'; GOLD='#C8960C'

# ── ページ生成ヘルパー ─────────────────────────────────────
_PN = [0]
def new_page(label='', title='', insight=''):
    _PN[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)
    if label:
        fig.text(0.04, 0.935, label, fontproperties=jf(8), color=TEXT2)
    if title:
        fig.text(0.04, 0.885, title, fontproperties=jf(18, bold=True), color=TEXT)
    if insight:
        fig.text(0.04, 0.840, insight, fontproperties=jf(9), color=TEXT2)
    div = fig.add_axes([0.04, 0.822, 0.92, 0.002])
    div.set_facecolor(TEAL); div.axis('off')
    fax = fig.add_axes([0, 0, 1, 0.075])
    fax.set_facecolor(FOOTER); fax.axis('off')
    fax.text(0.04, 0.5, '個別株パフォーマンス分析レポート  |  2026年6月19日現在',
             color=WHITE, fontproperties=jf(8), va='center')
    fax.text(0.97, 0.5, f'{_PN[0]}', color=WHITE, fontproperties=jf(9, bold=True),
             va='center', ha='right')
    return fig

def gs_body(fig, nrows=1, ncols=2, hspace=0.4, wspace=0.28, top=0.810, bottom=0.105):
    return GridSpec(nrows, ncols, figure=fig, left=0.04, right=0.97,
                    bottom=bottom, top=top, hspace=hspace, wspace=wspace)

def spine_clean(ax, bottom_only=True):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if bottom_only:
        ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)

def mtable(ax, headers, rows, col_w=None, fs=8.5, rs=1.6, bbox=None):
    ax.axis('off')
    if bbox is None:
        bbox = [0, 0, 1, 1]
    t = ax.table(cellText=rows, colLabels=headers,
                 colWidths=col_w, cellLoc='center', bbox=bbox)
    t.auto_set_font_size(False)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor(BORDER)
        cell.set_linewidth(0.5)
        if r == 0:
            cell.set_facecolor(HDRBG)
            cell.set_text_props(fontproperties=jf(fs, bold=True), color=TEXT)
        else:
            cell.set_facecolor(ALTBG if r % 2 == 0 else BG)
            cell.set_text_props(fontproperties=jf(fs), color=TEXT)
        cell.set_height(rs / 100)
    return t

# ────────────────────────────────────────────────────────────
# ── ポートフォリオデータ (2026/6/19現在, 口座合算) ──────────
# ────────────────────────────────────────────────────────────
JP = {
    '2124': {'name': 'JAC',        'cost':   970960, 'value':  1804120, 'pnl':   833160},
    '2169': {'name': 'CDS',        'cost':   533466, 'value':   583416, 'pnl':    49950},
    '4063': {'name': '信越化学',    'cost':   428300, 'value':   731000, 'pnl':   302700},
    '4502': {'name': '武田薬品',    'cost':   826760, 'value':  1085480, 'pnl':   258720},
    '6073': {'name': 'アサンテ',    'cost':    69806, 'value':    53770, 'pnl':   -16036},
    '6087': {'name': 'アビスト',    'cost':    36444, 'value':    39960, 'pnl':     3516},
    '7751': {'name': 'キヤノン',    'cost':   487300, 'value':   431000, 'pnl':   -56300},
    '7995': {'name': 'バルカー',    'cost':    33408, 'value':   128960, 'pnl':    95552},
    '8001': {'name': '伊藤忠',      'cost':    71085, 'value':   193988, 'pnl':   122902},
    '8031': {'name': '三井物産',    'cost':   600048, 'value':  2037312, 'pnl':  1437264},
    '8058': {'name': '三菱商事',    'cost':   605368, 'value':  1153160, 'pnl':   547792},
    '8306': {'name': '三菱UFJ',     'cost':   115432, 'value':   616264, 'pnl':   500832},
    '8316': {'name': '三井住友',    'cost':    52689, 'value':   252798, 'pnl':   200109},
    '8584': {'name': 'ジャックス',  'cost':   268300, 'value':   352000, 'pnl':    83700},
    '8591': {'name': 'オリックス',  'cost':   352027, 'value':  1068925, 'pnl':   716898},
    '8593': {'name': '三菱HCキャピ','cost':    14960, 'value':    28864, 'pnl':    13904},
    '8750': {'name': '第一生命HD',  'cost':    33024, 'value':   116128, 'pnl':    83104},
    '8766': {'name': '東京海上HD',  'cost':    32436, 'value':   129492, 'pnl':    97056},
    '8771': {'name': 'Eギャランティ','cost':   661600, 'value':   839500, 'pnl':   177900},
    '9142': {'name': 'JR九州',      'cost':    21488, 'value':    27480, 'pnl':     5992},
    '9432': {'name': 'NTT',         'cost':  1610650, 'value':  1707530, 'pnl':    96880},
    '9433': {'name': 'KDDI',        'cost':   363792, 'value':   576958, 'pnl':   213166},
    '9436': {'name': '沖縄セルラー','cost':    10384, 'value':    29200, 'pnl':    18816},
    '9986': {'name': '蔵王産業',    'cost':   934727, 'value':  1404089, 'pnl':   469362},
}
for code, s in JP.items():
    s['ret'] = s['pnl'] / s['cost'] * 100

US = {
    'AMBQ': {'name': 'Ambiq Micro', 'ret_usd': (90.48-34.98)/34.98*100,
             'value_jpy': 1168350, 'pnl_jpy': 752830, 'cost_jpy': 415520},
    'SKYT': {'name': 'SkyWater Tech','ret_usd': (36.57-5.39)/5.39*100,
             'value_jpy': 2656243, 'pnl_jpy': 2293993, 'cost_jpy': 362250},
    'PLTR': {'name': 'Palantir',     'ret_usd': (128.47-72.00)/72.00*100,
             'value_jpy': 145154, 'pnl_jpy': 68112, 'cost_jpy': 77042},
}
for t, s in US.items():
    s['ret_jpy'] = s['pnl_jpy'] / s['cost_jpy'] * 100

# ────────────────────────────────────────────────────────────
# ── 配当データ解析 ──────────────────────────────────────────
# ────────────────────────────────────────────────────────────
DIV_CSV = 'data/DISTRIBUTION_20260627095220.csv'

def parse_dividends(filepath):
    """Returns {code: {year: total_jpy}} and {code: [(date,qty,per_share)]}"""
    annual   = defaultdict(lambda: defaultdict(float))
    per_share_hist = defaultdict(list)
    with open(filepath, encoding='cp932', errors='replace') as f:
        for line in f:
            line = line.strip()
            parts = re.findall(r'"([^"]*)"', line)
            if len(parts) < 6:
                continue
            date, _, product, name_code = parts[0], parts[1], parts[2], parts[3]
            qty_str, amt_str = parts[4], parts[5]
            if not re.match(r'\d{4}/\d{1,2}/\d{1,2}', date):
                continue
            if product != '国内株式(現物)':
                continue
            words = name_code.split()
            code = words[-1] if words and re.match(r'^\d{4}$', words[-1]) else None
            if not code:
                continue
            qty = int(qty_str.replace(',', '')) if qty_str else 0
            amt = float(amt_str.replace(',', '')) if amt_str else 0.0
            if qty <= 0 or amt <= 0:
                continue
            year = int(date[:4])
            annual[code][year] += amt
            per_share_hist[code].append((date, qty, round(amt / qty, 1)))
    return annual, per_share_hist

div_annual, div_ps_hist = parse_dividends(DIV_CSV)

# 1株あたり年間配当 (各期の per-share を年集計)
def annual_per_share(code):
    """Returns {year: total_per_share_equiv} using actual qty at each payment"""
    by_year = defaultdict(float)
    for date, qty, ps in div_ps_hist[code]:
        yr = int(date[:4])
        by_year[yr] += ps
    return by_year

# 配当成長率 2023→2025 (年次合計ベース)
def div_growth_23_25(code):
    d23 = div_annual[code].get(2023, 0)
    d25 = div_annual[code].get(2025, 0)
    if d23 > 0 and d25 > 0:
        return (d25 - d23) / d23 * 100
    return None

# 前年同期比: 2026上期 vs 2025上期 (1〜6月の合計)
def div_h1_growth(code):
    """Compare Jan-Jun 2025 vs Jan-Jun 2026 (same half)"""
    h25 = sum(amt for date, qty, ps in div_ps_hist[code]
              if date.startswith('2025/') and int(date.split('/')[1]) <= 6
              for amt in [ps * qty])
    h26 = sum(amt for date, qty, ps in div_ps_hist[code]
              if date.startswith('2026/') and int(date.split('/')[1]) <= 6
              for amt in [ps * qty])
    if h25 > 0 and h26 > 0:
        return (h26 - h25) / h25 * 100
    return None

# 同月配当 per-share 比較 (前年同期)
def h1_ps_compare(code):
    """Returns (prev_period_ps, curr_period_ps) for the latest comparable payments"""
    entries = sorted(div_ps_hist[code], key=lambda x: x[0])
    # group by month pattern to find matching months across years
    from collections import defaultdict
    by_month = defaultdict(list)
    for date, qty, ps in entries:
        y, m = int(date[:4]), int(date.split('/')[1])
        by_month[m].append((y, ps))
    # find month with both 2025 and 2026 entries
    for m in sorted(by_month.keys()):
        ys = {y: ps for y, ps in by_month[m]}
        if 2025 in ys and 2026 in ys:
            return ys[2025], ys[2026], m
    return None

# 1株あたり配当成長率 (最新比較可能2期)
def ps_growth(code):
    ps = annual_per_share(code)
    years_avail = sorted(k for k in ps if k in [2022,2023,2024,2025])
    if len(years_avail) >= 2:
        y0, y1 = years_avail[0], years_avail[-1]
        if ps[y0] > 0 and ps[y1] > 0:
            n = y1 - y0
            cagr = ((ps[y1]/ps[y0]) ** (1/n) - 1) * 100 if n > 0 else 0
            return round(ps[y0], 1), round(ps[y1], 1), round(cagr, 1), y0, y1
    return None

# ────────────────────────────────────────────────────────────
# ── ページ 1: カバー ─────────────────────────────────────────
# ────────────────────────────────────────────────────────────
def s1_cover():
    fig = new_page()

    # タイトルブロック
    fig.text(0.50, 0.72, '個別株\nパフォーマンス分析', fontproperties=jf(34, bold=True),
             color=TEXT, ha='center', va='center', linespacing=1.3)
    fig.text(0.50, 0.56, '資産評価損益 × 配当成長の総合評価レポート',
             fontproperties=jf(13), color=TEXT2, ha='center')
    fig.text(0.50, 0.49, '2026年6月19日現在  |  SBI証券保有個別株',
             fontproperties=jf(10), color=TEXT2, ha='center')

    # 区切り線
    ln = fig.add_axes([0.20, 0.455, 0.60, 0.002])
    ln.set_facecolor(TEAL); ln.axis('off')

    # サマリーカード (top 3 capital, top 3 dividend growth)
    top3_cap = sorted(JP.items(), key=lambda x: x[1]['ret'], reverse=True)[:3]
    top3_div = [(c, div_growth_23_25(c)) for c in JP
                if div_growth_23_25(c) is not None]
    top3_div = sorted(top3_div, key=lambda x: x[1], reverse=True)[:3]

    card_data = [
        (TEAL, '評価損益 TOP3', [(JP[c]['name'], f"+{JP[c]['ret']:.0f}%") for c,_ in top3_cap]),
        (AMBER, '配当成長 TOP3 (2023→2025)', [(JP[c]['name'], f"+{g:.0f}%") for c,g in top3_div]),
    ]
    for i, (clr, title, items) in enumerate(card_data):
        x0 = 0.10 + i * 0.48
        ax = fig.add_axes([x0, 0.14, 0.40, 0.28])
        ax.set_facecolor(WHITE); ax.axis('off')
        ax.add_patch(FancyBboxPatch((0,0),1,1, boxstyle='round,pad=0.02',
                                    lw=1.5, edgecolor=clr, facecolor=WHITE,
                                    transform=ax.transAxes))
        ax.add_patch(Rectangle((0,0.82),1,0.18, color=clr, transform=ax.transAxes))
        ax.text(0.5, 0.905, title, ha='center', va='center',
                fontproperties=jf(9.5, bold=True), color=WHITE, transform=ax.transAxes)
        for j, (name, val) in enumerate(items):
            medal = ['🥇','🥈','🥉'][j] if False else f'{j+1}.'
            y = 0.60 - j*0.22
            ax.text(0.08, y, f'{j+1}.', fontproperties=jf(11, bold=True),
                    color=clr, va='center', transform=ax.transAxes)
            ax.text(0.22, y, name, fontproperties=jf(11), color=TEXT,
                    va='center', transform=ax.transAxes)
            ax.text(0.92, y, val, fontproperties=jf(12, bold=True),
                    color=clr, va='center', ha='right', transform=ax.transAxes)

    return fig

# ────────────────────────────────────────────────────────────
# ── ページ 2: 評価損益ランキング ─────────────────────────────
# ────────────────────────────────────────────────────────────
def s2_capital_return():
    fig = new_page(
        label='PERFORMANCE ANALYSIS  >  CAPITAL RETURN',
        title='評価損益ランキング',
        insight='取得コストに対する評価損益率。JP個別株24銘柄 + US個別株3銘柄を比較。'
    )
    gs = gs_body(fig, 1, 2, wspace=0.35)

    # ── 左: JP株 横棒グラフ ──
    ax = fig.add_subplot(gs[0, 0])
    ax.set_facecolor(BG)

    jp_sorted = sorted(JP.items(), key=lambda x: x[1]['ret'])
    codes   = [c for c,_ in jp_sorted]
    names   = [JP[c]['name'] for c in codes]
    rets    = [JP[c]['ret']  for c in codes]
    colors  = [POS if r >= 0 else NEG for r in rets]

    y_pos = np.arange(len(names))
    bars  = ax.barh(y_pos, rets, color=colors, height=0.7, edgecolor='none')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontproperties=jf(8), color=TEXT)
    ax.axvline(0, color=BORDER, lw=0.8)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'{x:+.0f}%'))
    spine_clean(ax, bottom_only=False)
    ax.tick_params(axis='x', labelsize=7.5, colors=TEXT2)
    ax.grid(axis='x', color=BORDER, lw=0.4, alpha=0.7)
    ax.set_xlabel('評価損益率 (%)', fontproperties=jf(8), color=TEXT2)
    ax.set_title('JP個別株 (24銘柄)', fontproperties=jf(9.5, bold=True),
                 color=TEXT, pad=6)

    # 値ラベル
    for i, (r, bar) in enumerate(zip(rets, bars)):
        ha  = 'left' if r >= 0 else 'right'
        x   = r + (2 if r >= 0 else -2)
        clr = POS if r >= 0 else NEG
        ax.text(x, i, f'{r:+.0f}%', va='center', ha=ha,
                fontproperties=jf(7.5, bold=True), color=clr)

    # ── 右: US株 + テーブル ──
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(BG)

    us_items = sorted(US.items(), key=lambda x: x[1]['ret_usd'], reverse=True)
    tickers  = [t for t,_ in us_items]
    us_names = [US[t]['name'] for t in tickers]
    us_rets  = [US[t]['ret_usd'] for t in tickers]

    y_pos2 = np.arange(len(tickers))
    ax2.barh(y_pos2, us_rets, color=POS, height=0.5, edgecolor='none')
    ax2.set_yticks(y_pos2)
    ax2.set_yticklabels([f'{t}' for t in tickers], fontproperties=jf(9), color=TEXT)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'{x:+.0f}%'))
    spine_clean(ax2, bottom_only=False)
    ax2.tick_params(axis='x', labelsize=8, colors=TEXT2)
    ax2.grid(axis='x', color=BORDER, lw=0.4, alpha=0.7)
    ax2.set_title('US個別株 (USD建てリターン)', fontproperties=jf(9.5, bold=True),
                  color=TEXT, pad=6)
    for i, r in enumerate(us_rets):
        ax2.text(r+3, i, f'{r:+.0f}%', va='center', ha='left',
                 fontproperties=jf(9, bold=True), color=POS)

    # US テーブル (評価額・損益 JPY)
    tbl_ax = fig.add_axes([0.545, 0.105, 0.42, 0.30])
    hdrs = ['Ticker', '評価額(万円)', '損益(万円)', '損益率(円)']
    rows = [[t, f'{US[t]["value_jpy"]/1e4:.0f}万',
             f'+{US[t]["pnl_jpy"]/1e4:.0f}万',
             f'+{US[t]["ret_jpy"]:.0f}%'] for t in tickers]
    mtable(tbl_ax, hdrs, rows, col_w=[0.22, 0.26, 0.26, 0.26], fs=8.5, rs=1.8,
           bbox=[0, 0, 1, 1])

    return fig

# ────────────────────────────────────────────────────────────
# ── ページ 3: 配当実績 年別推移 ─────────────────────────────
# ────────────────────────────────────────────────────────────
def s3_dividend_history():
    fig = new_page(
        label='PERFORMANCE ANALYSIS  >  DIVIDEND HISTORY',
        title='配当受取実績 年別推移',
        insight='各年の国内個別株配当受取額合計（税引後）。口座合算・JP個別株のみ。'
    )
    gs = gs_body(fig, 1, 2, wspace=0.32)

    YEARS = [2022, 2023, 2024, 2025]
    YEAR_COLS = [BLUE2, BLUE1, TEAL, AMBER]

    # 有意な配当実績がある銘柄のみ (2025年実績あり)
    codes_with_div = [c for c in JP if div_annual[c].get(2025, 0) > 0]

    # 配当実績テーブル(左) — 2026上期列を追加
    ax_tbl = fig.add_subplot(gs[0, 0])
    hdrs = ['銘柄', '2023', '2024', '2025', '2026上期', '前年同期比']
    rows = []
    for c in sorted(codes_with_div,
                    key=lambda x: div_annual[x].get(2025, 0), reverse=True):
        name = JP[c]['name']
        vals = [div_annual[c].get(y, 0) for y in [2023, 2024, 2025]]
        v26  = div_annual[c].get(2026, 0)
        h1g  = div_h1_growth(c)
        h1g_str = f'+{h1g:.0f}%' if h1g and h1g > 0 else \
                  (f'{h1g:.0f}%'  if h1g else '―')
        row = [name] \
            + [f'{v:,.0f}' if v > 0 else '―' for v in vals] \
            + [f'{v26:,.0f}' if v26 > 0 else '―', h1g_str]
        rows.append(row)
    mtable(ax_tbl, hdrs, rows,
           col_w=[0.20, 0.14, 0.14, 0.14, 0.14, 0.16],
           fs=7.5, rs=1.55, bbox=[0, 0, 1, 1])
    ax_tbl.set_title('年別配当受取額 (円, 税引後)  ※2026は1〜6月現在',
                     fontproperties=jf(9.0, bold=True), color=TEXT, pad=6)

    # 棒グラフ (右) — 2026上期を点線枠バーで追加
    top_codes = sorted(codes_with_div,
                       key=lambda x: div_annual[x].get(2025, 0), reverse=True)[:12]
    ax_bar = fig.add_subplot(gs[0, 1])
    ax_bar.set_facecolor(BG)

    n      = len(top_codes)
    bar_h  = 0.15
    PLOT_YEARS = [2023, 2024, 2025, 2026]
    PLOT_COLS  = [BLUE1, TEAL, AMBER, PURPLE]
    offsets = np.array([-1.5, -0.5, 0.5, 1.5]) * bar_h

    for yi, (y, col) in enumerate(zip(PLOT_YEARS, PLOT_COLS)):
        vals = [div_annual[c].get(y, 0) / 1000 for c in top_codes]
        ypos = np.arange(n) + offsets[yi]
        if y == 2026:
            # 2026は上期のみ: ハッチングで区別
            ax_bar.barh(ypos, vals, height=bar_h, color=col, label='2026上期',
                        edgecolor=col, lw=0.8, hatch='//', alpha=0.65)
        else:
            ax_bar.barh(ypos, vals, height=bar_h, color=col, label=f'{y}年',
                        edgecolor='none', alpha=0.9)

    ax_bar.set_yticks(np.arange(n))
    ax_bar.set_yticklabels([JP[c]['name'] for c in top_codes],
                            fontproperties=jf(8), color=TEXT)
    ax_bar.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'{x:.0f}K'))
    spine_clean(ax_bar, bottom_only=False)
    ax_bar.tick_params(axis='x', labelsize=7.5, colors=TEXT2)
    ax_bar.grid(axis='x', color=BORDER, lw=0.4, alpha=0.7)
    ax_bar.set_xlabel('配当受取額 (千円)', fontproperties=jf(8), color=TEXT2)
    ax_bar.set_title('上位12銘柄 配当推移 (2026上期含む)',
                     fontproperties=jf(9.0, bold=True), color=TEXT, pad=6)
    ax_bar.legend(prop=jf(7.5), framealpha=0.8, loc='lower right',
                  ncol=2, handlelength=1.2, columnspacing=0.8)

    return fig

# ────────────────────────────────────────────────────────────
# ── ページ 4: 配当成長率 & 1株あたり推移 ─────────────────────
# ────────────────────────────────────────────────────────────
def s4_dividend_growth():
    fig = new_page(
        label='PERFORMANCE ANALYSIS  >  DIVIDEND GROWTH',
        title='配当成長率ランキング',
        insight='左: 前年同期比（2025年上期 vs 2026年上期）。右: 1株あたり配当CAGR（税引後年次合算）。'
    )
    gs = gs_body(fig, 1, 2, wspace=0.35)

    # ── 左: 前年同期比 成長率（2025H1 vs 2026H1）──
    codes_h1 = [(c, div_h1_growth(c)) for c in JP if div_h1_growth(c) is not None]
    codes_h1 = sorted(codes_h1, key=lambda x: x[1])
    c_list  = [c for c,_ in codes_h1]
    g_list  = [g for _,g in codes_h1]
    colors_g = [POS if g >= 0 else NEG for g in g_list]

    ax_g = fig.add_subplot(gs[0, 0])
    ax_g.set_facecolor(BG)
    y_pos = np.arange(len(c_list))
    ax_g.barh(y_pos, g_list, color=colors_g, height=0.6, edgecolor='none')
    ax_g.set_yticks(y_pos)
    ax_g.set_yticklabels([JP[c]['name'] for c in c_list],
                          fontproperties=jf(8.5), color=TEXT)
    ax_g.axvline(0, color=BORDER, lw=0.8)
    ax_g.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'{x:+.0f}%'))
    spine_clean(ax_g, bottom_only=False)
    ax_g.tick_params(axis='x', labelsize=7.5, colors=TEXT2)
    ax_g.grid(axis='x', color=BORDER, lw=0.4, alpha=0.7)
    ax_g.set_xlabel('前年同期比 (2025上期→2026上期)', fontproperties=jf(8), color=TEXT2)
    ax_g.set_title('配当成長率 前年同期比 (2025上期→2026上期)',
                   fontproperties=jf(9.0, bold=True), color=TEXT, pad=6)

    # 値ラベル
    for i, (g, c_code) in enumerate(zip(g_list, c_list)):
        ha = 'left' if g >= 0 else 'right'
        x  = g + (1 if g >= 0 else -1)
        clr = POS if g >= 0 else NEG
        ax_g.text(x, i, f'{g:+.0f}%', va='center', ha=ha,
                  fontproperties=jf(7.5, bold=True), color=clr)

    # ── 右: 1株あたり配当推移テーブル ──
    ax_t = fig.add_subplot(gs[0, 1])
    ps_data = []
    for c in JP:
        r = ps_growth(c)
        if r:
            old_ps, new_ps, cagr, y0, y1 = r
            ps_data.append((c, JP[c]['name'], old_ps, new_ps, cagr, y0, y1))

    # sort by CAGR desc
    ps_data.sort(key=lambda x: x[4], reverse=True)

    hdrs = ['銘柄', '基準年', '1株配当', '最新年', '1株配当', 'CAGR']
    rows = [[d[1], str(d[5]), f'{d[2]:.1f}円',
             str(d[6]), f'{d[3]:.1f}円',
             f'+{d[4]:.1f}%' if d[4] >= 0 else f'{d[4]:.1f}%']
            for d in ps_data]
    mtable(ax_t, hdrs, rows, col_w=[0.22,0.10,0.14,0.10,0.14,0.13],
           fs=8.0, rs=1.55, bbox=[0, 0, 1, 1])
    ax_t.set_title('1株あたり配当 CAGR (税引後・年次合算)',
                   fontproperties=jf(9.5, bold=True), color=TEXT, pad=6)

    # 注釈
    fig.text(0.97, 0.10, '※株式分割銘柄は分割前後でper-shareが非連続になる場合あり',
             fontproperties=jf(7), color=TEXT2, ha='right')

    return fig

# ────────────────────────────────────────────────────────────
# ── ページ 5: 総合パフォーマンス分析 ────────────────────────
# ────────────────────────────────────────────────────────────
def s5_summary():
    fig = new_page(
        label='PERFORMANCE ANALYSIS  >  COMPREHENSIVE SCORE',
        title='総合パフォーマンス分析',
        insight='評価損益率(横軸) × 配当成長率(縦軸)で各銘柄を4象限に分類。右上が総合優秀銘柄。'
    )
    gs = gs_body(fig, 1, 2, wspace=0.35)

    # ── 左: 散布図 (4象限) ──
    ax = fig.add_subplot(gs[0, 0])
    ax.set_facecolor(BG)

    # 前年同期比が取れる銘柄を優先、なければ2023→2025成長率を使用
    codes_both, x_vals, y_vals, y_labels = [], [], [], []
    for c in JP:
        h1g = div_h1_growth(c)
        g23 = div_growth_23_25(c)
        g   = h1g if h1g is not None else g23
        if g is not None:
            codes_both.append(c)
            x_vals.append(JP[c]['ret'])
            y_vals.append(g)
            y_labels.append('前年同期比' if h1g is not None else '2023-25')

    med_x = np.median(x_vals)
    med_y = np.median(y_vals)

    # 象限背景
    xlim = (-35, 460); ylim = (-25, 310)
    ax.fill_betweenx([med_y, ylim[1]], xlim[0], med_x,
                     color='#E8F4EE', alpha=0.5, zorder=0)
    ax.fill_betweenx([med_y, ylim[1]], med_x, xlim[1],
                     color='#E8F4F9', alpha=0.6, zorder=0)
    ax.fill_betweenx([ylim[0], med_y], xlim[0], med_x,
                     color='#F5F2EE', alpha=0.4, zorder=0)
    ax.fill_betweenx([ylim[0], med_y], med_x, xlim[1],
                     color='#FFF8EC', alpha=0.5, zorder=0)

    # 中央線
    ax.axvline(med_x, color=BORDER, lw=0.8, ls='--', alpha=0.7)
    ax.axhline(med_y, color=BORDER, lw=0.8, ls='--', alpha=0.7)

    # 象限ラベル
    ax.text(xlim[1]*0.95, ylim[1]*0.93, '★スター銘柄', ha='right',
            fontproperties=jf(8, bold=True), color=TEAL, alpha=0.8, transform=ax.transData)
    ax.text(xlim[0]+5,    ylim[1]*0.93, '配当成長型',
            fontproperties=jf(8), color=POS, alpha=0.7)
    ax.text(xlim[1]*0.95, ylim[0]+5,    'キャピタル型', ha='right',
            fontproperties=jf(8), color=AMBER, alpha=0.7)
    ax.text(xlim[0]+5,    ylim[0]+5,    '要検討',
            fontproperties=jf(8), color=NEG, alpha=0.7)

    # プロット
    for c, x, y in zip(codes_both, x_vals, y_vals):
        clr = TEAL if (x > med_x and y > med_y) else \
              POS  if y > med_y else \
              AMBER if x > med_x else NEG
        ax.scatter(x, y, color=clr, s=60, zorder=5, edgecolor=WHITE, lw=0.8)
        ax.text(x+4, y+2, JP[c]['name'], fontproperties=jf(6.5), color=TEXT, zorder=6)

    # JP最高は別途
    for c in codes_both:
        if JP[c]['ret'] > 300:
            x, y = JP[c]['ret'], div_growth_23_25(c)

    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:+.0f}%'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:+.0f}%'))
    spine_clean(ax, bottom_only=False)
    ax.tick_params(axis='both', labelsize=7.5, colors=TEXT2)
    ax.set_xlabel('評価損益率', fontproperties=jf(8), color=TEXT2)
    ax.set_ylabel('配当成長率 (前年同期比 or 2023→2025)', fontproperties=jf(8), color=TEXT2)
    ax.set_title('散布図: 資本成長 × 配当成長',
                 fontproperties=jf(9.5, bold=True), color=TEXT, pad=6)
    ax.grid(color=BORDER, lw=0.4, alpha=0.5)

    # ── 右: 総合スコア表 ──
    ax_t = fig.add_subplot(gs[0, 1])

    # スコア計算
    x_arr = np.array(x_vals)
    y_arr = np.array([v for v in y_vals])
    x_norm = (x_arr - x_arr.min()) / (x_arr.max() - x_arr.min() + 1e-9)
    y_norm = (y_arr - y_arr.min()) / (y_arr.max() - y_arr.min() + 1e-9)
    scores = [(c, 0.5*xn + 0.5*yn, JP[c]['ret'], gv)
              for c, xn, yn, gv in zip(codes_both, x_norm, y_norm, y_vals)]
    scores.sort(key=lambda x: x[1], reverse=True)

    hdrs = ['順位', '銘柄', '損益率', '配当成長', '基準', 'スコア']
    rows = []
    for rank, (c, sc, ret, gv) in enumerate(scores, 1):
        medal = {1:'◆', 2:'◇', 3:'△'}.get(rank, f'{rank}')
        h1g = div_h1_growth(c)
        basis = '前年同期' if h1g is not None else '23→25'
        rows.append([medal, JP[c]['name'],
                     f'+{ret:.0f}%' if ret >= 0 else f'{ret:.0f}%',
                     f'+{gv:.0f}%' if gv >= 0 else f'{gv:.0f}%',
                     basis,
                     f'{sc*100:.0f}pt'])
    mtable(ax_t, hdrs, rows, col_w=[0.08, 0.24, 0.15, 0.15, 0.15, 0.13],
           fs=7.8, rs=1.50, bbox=[0, 0, 1, 1])
    ax_t.set_title('総合スコアランキング (配当成長確認済み銘柄)',
                   fontproperties=jf(9.0, bold=True), color=TEXT, pad=6)

    fig.text(0.50, 0.10,
             '※配当成長は前年同期比(2025上期→2026上期)を優先、データ不足は2023→2025年次成長率を使用。',
             fontproperties=jf(7), color=TEXT2, ha='center')

    return fig

# ────────────────────────────────────────────────────────────
# ── ページ 6: 高パフォーマンス銘柄フォーカス ─────────────────
# ────────────────────────────────────────────────────────────
def s6_focus():
    """スター銘柄の詳細 - 評価損益 + 配当推移を1枚に"""
    fig = new_page(
        label='PERFORMANCE ANALYSIS  >  STAR STOCKS FOCUS',
        title='スター銘柄 詳細フォーカス',
        insight='評価損益率・配当成長率とも上位の注目銘柄。各銘柄の配当ヒストリーと資産推移を確認。'
    )

    # 注目銘柄 (高資本成長 & 配当データあり)
    focus_codes = ['8306', '8316', '8591', '8031', '8058', '2124']
    PLOT_YEARS = [2022, 2023, 2024, 2025, 2026]
    Y_COLS     = [BLUE2, BLUE1, TEAL, AMBER, PURPLE]
    X_LABELS   = ['22', '23', '24', '25', '26上']

    n = len(focus_codes)
    cols = 3
    rows_n = (n + cols - 1) // cols

    outer_gs = GridSpec(rows_n, cols, figure=fig, left=0.04, right=0.97,
                        bottom=0.105, top=0.810, hspace=0.55, wspace=0.32)

    for i, c in enumerate(focus_codes):
        r_idx, c_idx = divmod(i, cols)
        ax = fig.add_subplot(outer_gs[r_idx, c_idx])
        ax.set_facecolor(BG)

        vals = [div_annual[c].get(y, 0) / 1000 for y in PLOT_YEARS]
        has_any = any(v > 0 for v in vals)
        bar_colors = [col if v > 0 else BORDER for v, col in zip(vals, Y_COLS)]

        if has_any:
            x_pos = np.arange(len(PLOT_YEARS))
            bars = ax.bar(x_pos, vals, color=bar_colors, edgecolor='none', width=0.6)
            # 2026は上期なのでハッチング
            bars[-1].set_hatch('//')
            bars[-1].set_edgecolor(PURPLE)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}K'))
            ax.set_ylabel('配当(千円)', fontproperties=jf(7), color=TEXT2)
            for bar, v in zip(bars, vals):
                if v > 0:
                    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                            f'{v:.0f}K', ha='center', va='bottom',
                            fontproperties=jf(6.5), color=TEXT2)
        else:
            ax.text(0.5, 0.5, '配当データなし', ha='center', va='center',
                    fontproperties=jf(8), color=TEXT2, transform=ax.transAxes)

        spine_clean(ax, bottom_only=False)
        ax.tick_params(axis='both', labelsize=7, colors=TEXT2)
        ax.set_xticks(np.arange(len(PLOT_YEARS)))
        ax.set_xticklabels(X_LABELS, fontproperties=jf(7), color=TEXT2)

        ret   = JP[c]['ret']
        h1g   = div_h1_growth(c)
        g23   = div_growth_23_25(c)
        if h1g is not None:
            g_str = f'前年同期+{h1g:.0f}%' if h1g >= 0 else f'前年同期{h1g:.0f}%'
            clr_g = POS if h1g > 0 else NEG
        elif g23 is not None:
            g_str = f'23-25: {g23:+.0f}%'
            clr_g = POS if g23 > 0 else NEG
        else:
            g_str = '配当データ限定'
            clr_g = TEXT2
        clr = TEAL if (ret > 100 and (h1g or 0) > 0) else AMBER if ret > 100 else TEXT

        ax.set_title(f'{JP[c]["name"]} ({c})\n損益{ret:+.0f}%  {g_str}',
                     fontproperties=jf(8.5, bold=True), color=clr, pad=5,
                     linespacing=1.4)
        ax.grid(axis='y', color=BORDER, lw=0.4, alpha=0.6)

    return fig

# ────────────────────────────────────────────────────────────
# ── メイン実行 ──────────────────────────────────────────────
# ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs('output', exist_ok=True)
    OUT = 'output/stock_performance_v1.pdf'

    pages = [
        ('s1_cover',            s1_cover),
        ('s2_capital_return',   s2_capital_return),
        ('s3_dividend_history', s3_dividend_history),
        ('s4_dividend_growth',  s4_dividend_growth),
        ('s5_summary',          s5_summary),
        ('s6_focus',            s6_focus),
    ]

    imgs = []
    for name, fn in pages:
        print(f'  {len(imgs)+1}/{len(pages)}: {name}')
        fig = fn()
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=BG)
        plt.close(fig)
        buf.seek(0)
        imgs.append(Image.open(buf).convert('RGB'))

    imgs[0].save(OUT, save_all=True, append_images=imgs[1:], resolution=150)
    kb = os.path.getsize(OUT) // 1024
    print(f'\n✅  {OUT}  ({kb} KB)')
