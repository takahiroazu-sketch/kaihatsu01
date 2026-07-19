#!/usr/bin/env python3
"""配当金推移グラフ + 配当利回りマトリクス"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
import matplotlib.colors as mcolors
import numpy as np, os, re, csv as csvmod
from collections import defaultdict
from io import BytesIO
from PIL import Image

import matplotlib.font_manager as fm
_JP_CANDIDATES = [
    '/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
    '/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
    '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
    '/System/Library/Fonts/Supplemental/ヒラギノ角ゴシック W3.ttc',
    '/Library/Fonts/Osaka.ttf',
]
_jp_font = next((p for p in _JP_CANDIDATES if os.path.exists(p)), None)
def jf(size=10, bold=False):
    if _jp_font:
        prop = fm.FontProperties(fname=_jp_font, size=size)
        return prop
    return fm.FontProperties(size=size)

plt.rcParams['axes.unicode_minus'] = False

# === Design tokens (v4 approved) ===
BG     = '#EDEAE6'; TEXT   = '#1A1A1A'; TEXT2  = '#6B6560'
TEAL   = '#00B4CC'; BLUE1  = '#5BAED0'; BLUE2  = '#8EC8E8'
AMBER  = '#D4820C'; PURPLE = '#8870CC'; POS    = '#2D8A50'
NEG    = '#C03030'; FOOTER = '#1C1C1C'; WHITE  = '#FFFFFF'
HDRBG  = '#D4D0CC'; ALTBG  = '#F5F2EE'; BORDER = '#C8C4BE'

PLOT_YEARS = [2022, 2023, 2024, 2025, 2026]
YR_COLOR   = {2022: '#B0CEDE', 2023: BLUE2, 2024: BLUE1, 2025: TEAL, 2026: AMBER}

DATA_DIR  = '/Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri/data'
CSV_HIST  = f'{DATA_DIR}/DISTRIBUTION_20260627095220.csv'
CSV_2026  = f'{DATA_DIR}/DISTRIBUTION_20260629190814.csv'
PORT_CSV  = f'{DATA_DIR}/260619jp.csv'
OUT_DIR   = '/Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri/output'

DPI = 150
FIG_W, FIG_H = 11.69, 8.27  # A4 landscape

# ─── Data loading ────────────────────────────────────────────────────────────

def _read_div_csv(path, year_filter=None):
    recs = []
    with open(path, encoding='cp932', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: row = list(csvmod.reader([line]))[0]
            except: continue
            if len(row) < 6: continue
            if not re.match(r'^20\d\d/\d{1,2}/\d{1,2}$', row[0]): continue
            try:
                yr = int(row[0][:4])
                if year_filter and yr not in year_filter: continue
                qty = int(row[4].replace(',', '')) if row[4].strip() else 0
                amt = float(row[5].replace(',', '')) if row[5].strip() else 0.0
                if qty <= 0 or amt <= 0: continue
                if row[2] != '国内株式(現物)': continue
                words = row[3].split()
                code = words[-1] if words and re.match(r'^\d{4}$', words[-1]) else None
                if not code: continue
                recs.append({'date': row[0], 'year': yr,
                             'month': int(row[0].split('/')[1]),
                             'code': code, 'name': row[3],
                             'acct': row[1], 'qty': qty, 'amt': amt})
            except: continue
    return recs

recs = (_read_div_csv(CSV_HIST, {2021,2022,2023,2024,2025}) +
        _read_div_csv(CSV_2026,  {2026}))

# Annual totals per stock (all accounts combined)
by_code_year = defaultdict(lambda: defaultdict(float))
code_name    = {}
for r in recs:
    by_code_year[r['code']][r['year']] += r['amt']
    code_name[r['code']] = r['name']

# Stocks sorted by cumulative total (highest first)
all_codes = sorted(by_code_year, key=lambda c: sum(by_code_year[c].values()), reverse=True)

# Short display names
SHORT = {
    '2124':'JAC','2169':'CDS','4063':'信越化学','4502':'武田薬品',
    '6073':'アサンテ','6087':'アビスト','7751':'キヤノン','7995':'バルカー',
    '8001':'伊藤忠','8031':'三井物産','8058':'三菱商事','8306':'三菱UFJ',
    '8316':'三井住友','8584':'ジャックス','8591':'オリックス','8593':'三菱HCキャピ',
    '8750':'第一生命','8766':'東京海上','8771':'Eギャランティ','9142':'JR九州',
    '9432':'NTT','9433':'KDDI','9436':'沖縄セルラー','9504':'中国電力',
    '9986':'蔵王産業',
}
def sname(code):
    return SHORT.get(code, code_name.get(code, code)[:8])

# ─── Portfolio data ───────────────────────────────────────────────────────────

def _read_port_csv(path):
    """Parse portfolio CSV; track cost/value per account type for tax-aware gain calc."""
    port = defaultdict(lambda: {'qty':0,'cost':0.0,'value':0.0,'price':0.0,
                                'cost_ps':0.0,'nisa_gain':0.0,'taxable_gain':0.0})
    is_taxable = True
    with open(path, encoding='cp932', errors='replace') as f:
        for line in f:
            raw = line.strip()
            if not raw: continue
            if '特定預り' in raw and 'NISA' not in raw:
                is_taxable = True
            elif 'NISA' in raw or 'ＮＩＳＡ' in raw:
                is_taxable = False
            try: row = list(csvmod.reader([raw]))[0]
            except: continue
            if len(row) < 9: continue
            if not re.match(r'^\d{4}$', row[0].strip('"')): continue
            code = row[0].strip('"')
            try:
                qty   = int(row[2].replace(',',''))
                price = float(row[5].replace(',',''))
                cost  = float(row[6].replace(',',''))
                value = float(row[7].replace(',',''))
                gain  = value - cost
                port[code]['qty']   += qty
                port[code]['cost']  += cost
                port[code]['value'] += value
                if port[code]['qty'] > 0:
                    port[code]['price']   = price
                    port[code]['cost_ps'] = port[code]['cost'] / port[code]['qty']
                if is_taxable:
                    port[code]['taxable_gain'] += gain
                else:
                    port[code]['nisa_gain'] += gain
            except: continue
    # Compute blended after-tax capital gain (NISA=0%, 特定=20.315%)
    TAX = 0.20315
    for code in port:
        g_tax  = port[code]['taxable_gain']
        g_nisa = port[code]['nisa_gain']
        port[code]['after_tax_gain'] = g_nisa + g_tax * (1 - TAX)
    return port

port = _read_port_csv(PORT_CSV)

# ─── Yield computation ────────────────────────────────────────────────────────

# 2025 annual dividends per stock
div_2025 = {code: by_code_year[code].get(2025, 0.0) for code in all_codes}

def yield_on_cost(code):
    c = port[code]['cost']
    d = div_2025.get(code, 0)
    return d / c * 100 if c > 0 and d > 0 else None

def current_yield(code):
    v = port[code]['value']
    d = div_2025.get(code, 0)
    return d / v * 100 if v > 0 and d > 0 else None

# Stocks with dividend history for the matrix
div_codes = [c for c in all_codes if sum(by_code_year[c].values()) > 0]

# ─── Page rendering helpers ───────────────────────────────────────────────────

def make_fig():
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(BG)
    return fig

def dark_footer(fig, label, page, total):
    ax = fig.add_axes([0, 0, 1, 0.075])
    ax.set_facecolor(FOOTER)
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.axis('off')
    ax.text(0.025, 0.5, label,  color=WHITE, fontsize=9, va='center', fontproperties=jf(9))
    ax.text(0.975, 0.5, f'{page}/{total}', color=TEXT2,  fontsize=8, va='center', ha='right',
            fontproperties=jf(8))

def page_header(fig, label, title, insight=''):
    ax = fig.add_axes([0, 0.82, 1, 0.18])
    ax.set_facecolor(BG); ax.axis('off')
    ax.text(0.025, 0.92, label, color=TEAL, fontsize=9, fontweight='bold',
            fontproperties=jf(9, bold=True))
    ax.text(0.025, 0.62, title, color=TEXT, fontsize=16, fontweight='bold',
            fontproperties=jf(16, bold=True))
    if insight:
        ax.text(0.025, 0.30, insight, color=TEXT2, fontsize=9,
                fontproperties=jf(9))
    ax.axhline(0.04, color=BORDER, linewidth=0.8, xmin=0.025, xmax=0.975)

def fig_to_img(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=DPI, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).copy()
    buf.close()
    plt.close(fig)
    return img

# ─── Page 1: Small Multiples ─────────────────────────────────────────────────

def page_small_multiples():
    fig = make_fig()
    page_header(fig,
                '配当金推移分析  |  2022–2026上',
                '全銘柄  年別配当受取額推移',
                '各銘柄の年別受取配当金額（税引後）。2026は上半期（1–6月）の実績。棒の色が年度を示す。')

    codes = div_codes
    n = len(codes)
    ncols = 5
    nrows = int(np.ceil(n / ncols))

    # Content area: y=0.085 to y=0.818
    gs = GridSpec(nrows, ncols, figure=fig,
                  left=0.03, right=0.97, bottom=0.09, top=0.82,
                  hspace=0.55, wspace=0.35)

    bar_w = 0.65
    xs = np.arange(len(PLOT_YEARS))

    for i, code in enumerate(codes):
        row, col = divmod(i, ncols)
        ax = fig.add_subplot(gs[row, col])
        ax.set_facecolor(BG)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.tick_params(left=False, bottom=False)
        ax.yaxis.set_visible(False)

        vals = [by_code_year[code].get(y, 0) for y in PLOT_YEARS]
        colors = [YR_COLOR[y] for y in PLOT_YEARS]
        bars = ax.bar(xs, vals, width=bar_w, color=colors, zorder=3)

        # Label non-zero bars
        maxv = max(vals) if max(vals) > 0 else 1
        for j, (v, bar) in enumerate(zip(vals, bars)):
            if v > 0:
                label = f'{v/1000:.0f}k' if v >= 10000 else f'{v:.0f}'
                fs = 5.5 if v >= 10000 else 5
                ax.text(bar.get_x() + bar.get_width()/2, v + maxv*0.04,
                        label, ha='center', va='bottom', fontsize=fs,
                        color=TEXT2, fontproperties=jf(fs))

        yr_labels = [str(y)[-2:]+"'" if y < 2026 else '26上' for y in PLOT_YEARS]
        ax.set_xticks(xs)
        ax.set_xticklabels(yr_labels, fontsize=6, color=TEXT2,
                           fontproperties=jf(6))
        ax.set_xlim(-0.55, len(PLOT_YEARS)-0.45)
        ax.set_ylim(0, maxv * 1.30)

        cum = sum(vals)
        cum_str = f'{cum/10000:.1f}万' if cum >= 10000 else f'¥{cum:,.0f}'
        title_str = f'{sname(code)} [{code}]  累計{cum_str}'
        ax.set_title(title_str, fontsize=7, color=TEXT, pad=3,
                     fontproperties=jf(7), loc='left')
        ax.grid(axis='y', color=BORDER, linewidth=0.4, alpha=0.6, zorder=1)

    # Legend
    legend_ax = fig.add_axes([0.03, 0.075, 0.94, 0.016])
    legend_ax.set_facecolor(BG); legend_ax.axis('off')
    handles = [mpatches.Patch(facecolor=YR_COLOR[y],
                              label=f"{y}年{'（上半期）' if y==2026 else ''}") for y in PLOT_YEARS]
    legend_ax.legend(handles=handles, loc='center', ncol=len(PLOT_YEARS),
                     frameon=False, fontsize=7,
                     prop=jf(7))

    dark_footer(fig, '個人資産管理  |  配当分析レポート', 1, 3)
    return fig_to_img(fig)

# ─── Page 2: Heatmap ─────────────────────────────────────────────────────────

def page_heatmap():
    fig = make_fig()
    page_header(fig,
                '配当利回りマトリクス  |  年別配当ヒートマップ',
                '1株あたり相当  年別受取額ヒートマップ',
                '各銘柄・各年の受取配当総額。色が濃いほど受取額が多い。右側に2025年実績ベースの利回りを表示。')

    # Build matrix data
    YEARS_M = [2022, 2023, 2024, 2025, 2026]
    n_stocks = len(div_codes)
    n_years  = len(YEARS_M)

    mat = np.zeros((n_stocks, n_years))
    for i, code in enumerate(div_codes):
        for j, yr in enumerate(YEARS_M):
            mat[i, j] = by_code_year[code].get(yr, 0)

    # Normalize for color (per-row max)
    mat_norm = np.zeros_like(mat)
    for i in range(n_stocks):
        rmax = mat[i].max()
        if rmax > 0:
            mat_norm[i] = mat[i] / rmax

    # Heatmap axes: left 65%, table right 35%
    ax_hm = fig.add_axes([0.03, 0.095, 0.62, 0.715])
    ax_hm.set_facecolor(BG)

    # Teal colormap
    teal_cmap = mcolors.LinearSegmentedColormap.from_list(
        'teal_seq', ['#EEF8FB', '#00B4CC', '#005060'], N=256)

    for i in range(n_stocks):
        for j in range(n_years):
            v_norm = mat_norm[i, j]
            color = teal_cmap(v_norm)
            rect = plt.Rectangle([j - 0.48, n_stocks - i - 1 - 0.48],
                                  0.96, 0.96, color=color)
            ax_hm.add_patch(rect)
            v = mat[i, j]
            if v > 0:
                label = f'{v/10000:.1f}万' if v >= 10000 else f'{v:,.0f}'
                txt_color = WHITE if v_norm > 0.55 else TEXT
                ax_hm.text(j, n_stocks - i - 1, label,
                           ha='center', va='center', fontsize=7,
                           color=txt_color, fontproperties=jf(7))

    ax_hm.set_xlim(-0.55, n_years - 0.45)
    ax_hm.set_ylim(-0.55, n_stocks - 0.45)
    ax_hm.set_xticks(range(n_years))
    ax_hm.set_xticklabels(['2022', '2023', '2024', '2025', '2026上'],
                           fontsize=9, color=TEXT, fontproperties=jf(9))
    ax_hm.set_yticks(range(n_stocks))
    ax_hm.set_yticklabels([sname(c) for c in reversed(div_codes)],
                           fontsize=8, color=TEXT, fontproperties=jf(8))
    ax_hm.tick_params(left=False, bottom=False)
    for sp in ax_hm.spines.values(): sp.set_visible(False)

    # Grid lines between cells
    for j in range(n_years + 1):
        ax_hm.axvline(j - 0.5, color=BG, linewidth=1.5, zorder=5)
    for i in range(n_stocks + 1):
        ax_hm.axhline(i - 0.5, color=BG, linewidth=1.5, zorder=5)

    # ─ Yield table on right ─
    ax_tbl = fig.add_axes([0.67, 0.095, 0.31, 0.715])
    ax_tbl.set_facecolor(BG)
    ax_tbl.axis('off')
    ax_tbl.set_xlim(0, 1)
    ax_tbl.set_ylim(0, n_stocks + 0.8)

    # Header
    hdr_y = n_stocks + 0.2
    ax_tbl.text(0.00, hdr_y, '銘柄',      fontsize=8, color=TEXT,  fontproperties=jf(8, True), va='bottom')
    ax_tbl.text(0.45, hdr_y, '2025配当',  fontsize=8, color=TEXT,  fontproperties=jf(8, True), va='bottom', ha='right')
    ax_tbl.text(0.70, hdr_y, 'コスト利回', fontsize=8, color=TEXT,  fontproperties=jf(8, True), va='bottom', ha='right')
    ax_tbl.text(1.00, hdr_y, '現在利回',  fontsize=8, color=TEXT,  fontproperties=jf(8, True), va='bottom', ha='right')
    ax_tbl.axhline(n_stocks - 0.05, color=BORDER, linewidth=0.8)

    # Sort codes by コスト利回り for table display
    def sort_key(c):
        yc = yield_on_cost(c)
        return yc if yc else 0
    tbl_codes = sorted(div_codes, key=sort_key, reverse=True)

    for idx, code in enumerate(tbl_codes):
        row_y = n_stocks - idx - 1
        bg_col = ALTBG if idx % 2 == 0 else BG
        ax_tbl.add_patch(plt.Rectangle([0, row_y - 0.4], 1, 0.85,
                                        facecolor=bg_col, edgecolor='none', zorder=0))
        d2025 = div_2025.get(code, 0)
        yc    = yield_on_cost(code)
        yp    = current_yield(code)

        ax_tbl.text(0.00, row_y, sname(code),
                    fontsize=7.5, color=TEXT, va='center', fontproperties=jf(7.5))
        d_str = f'{d2025/10000:.1f}万' if d2025 >= 10000 else (f'{d2025:,.0f}' if d2025 > 0 else '-')
        ax_tbl.text(0.45, row_y, d_str,
                    fontsize=7.5, color=TEXT, va='center', ha='right', fontproperties=jf(7.5))
        if yc:
            col = POS if yc >= 3 else (AMBER if yc >= 2 else TEXT2)
            ax_tbl.text(0.70, row_y, f'{yc:.1f}%',
                        fontsize=8, color=col, va='center', ha='right',
                        fontproperties=jf(8, True), fontweight='bold')
        else:
            ax_tbl.text(0.70, row_y, '-', fontsize=7.5, color=TEXT2, va='center',
                        ha='right', fontproperties=jf(7.5))
        if yp:
            col = POS if yp >= 3 else (AMBER if yp >= 2 else TEXT2)
            ax_tbl.text(1.00, row_y, f'{yp:.1f}%',
                        fontsize=8, color=col, va='center', ha='right',
                        fontproperties=jf(8, True), fontweight='bold')
        else:
            ax_tbl.text(1.00, row_y, '-', fontsize=7.5, color=TEXT2, va='center',
                        ha='right', fontproperties=jf(7.5))

    ax_tbl.set_title('配当利回り一覧（2025年実績）', fontsize=9, color=TEXT,
                     fontproperties=jf(9, True), loc='center', pad=4)

    dark_footer(fig, '個人資産管理  |  配当分析レポート', 2, 3)
    return fig_to_img(fig)

# ─── Page 3: Yield Ranking + Total Return ────────────────────────────────────

def page_yield_ranking():
    fig = make_fig()
    page_header(fig,
                '配当利回り・トータルリターン  |  2025年実績',
                '配当利回りランキング  ＋  トータルリターン（売却時想定）',
                '左：年間配当利回り（2025年実績）。'
                '右：（受取配当累計＋税抜売却益）÷取得コスト。'
                '特定口座20.315%課税・NISA非課税適用。')

    # --- Left: yield by cost (2025) ---
    ranked = [(c, yield_on_cost(c), current_yield(c))
              for c in div_codes if yield_on_cost(c) is not None]
    ranked.sort(key=lambda x: x[1], reverse=True)
    n1 = len(ranked)

    ax1 = fig.add_axes([0.12, 0.115, 0.34, 0.695])
    ax1.set_facecolor(BG)
    for sp in ['top', 'right', 'left']: ax1.spines[sp].set_visible(False)
    ax1.spines['bottom'].set_color(BORDER)
    ax1.tick_params(left=False)

    ys1 = np.arange(n1)
    cost_yields = [r[1] for r in ranked]
    curr_yields = [r[2] if r[2] else 0 for r in ranked]
    bar_h = 0.30
    gap   = 0.06

    ax1.barh(ys1 + gap/2 + bar_h/2, curr_yields, height=bar_h, color=BLUE2, zorder=3)
    ax1.barh(ys1 - gap/2 - bar_h/2, cost_yields, height=bar_h,
             color=[POS if v >= 3 else (AMBER if v >= 2 else TEXT2) for v in cost_yields],
             zorder=4)

    for i, (r, vc, vp) in enumerate(zip(ranked, cost_yields, curr_yields)):
        ax1.text(vc + 0.10, i - gap/2 - bar_h/2, f'{vc:.1f}%',
                 va='center', fontsize=7.5, fontproperties=jf(7.5),
                 color=POS if vc >= 3 else (AMBER if vc >= 2 else TEXT2))
        if vp > 0:
            ax1.text(vp + 0.10, i + gap/2 + bar_h/2, f'{vp:.1f}%',
                     va='center', fontsize=6.5, color=BLUE1, fontproperties=jf(6.5))

    ax1.set_yticks(ys1)
    ax1.set_yticklabels([f'{sname(r[0])} [{r[0]}]' for r in ranked],
                        fontsize=8, color=TEXT, fontproperties=jf(8))
    ax1.set_xlabel('配当利回り（%）', fontsize=8, color=TEXT2, fontproperties=jf(8))
    ax1.set_xlim(0, max(cost_yields + curr_yields) * 1.45 + 0.3)
    ax1.set_ylim(-0.8, n1 - 0.2)
    ax1.invert_yaxis()
    ax1.tick_params(axis='x', colors=TEXT2, labelsize=7)
    ax1.axvline(3, color=POS,  linewidth=0.7, linestyle='--', alpha=0.5, zorder=2)
    ax1.axvline(2, color=AMBER, linewidth=0.7, linestyle='--', alpha=0.5, zorder=2)
    ax1.text(3.05, -0.65, '3%', fontsize=6.5, color=POS,  fontproperties=jf(6.5))
    ax1.text(2.05, -0.65, '2%', fontsize=6.5, color=AMBER, fontproperties=jf(6.5))
    ax1.grid(axis='x', color=BORDER, linewidth=0.4, alpha=0.7, zorder=1)
    ax1.set_title('年間配当利回り（2025年実績）', fontsize=9, color=TEXT,
                  fontproperties=jf(9, True), pad=6)

    # --- Right: total return (cumulative div + after-tax cap gain) / cost ---
    all_port_codes = sorted(port.keys(), key=lambda c: port[c]['cost'], reverse=False)
    total_ret_rows = []
    for code in all_port_codes:
        cost = port[code]['cost']
        if cost <= 0: continue
        cum_div   = sum(by_code_year[code].values())
        atg       = port[code]['after_tax_gain']
        div_ret   = cum_div / cost * 100
        cap_ret   = atg / cost * 100
        total_ret = div_ret + cap_ret
        total_ret_rows.append((code, total_ret, div_ret, cap_ret))

    total_ret_rows.sort(key=lambda x: x[1], reverse=True)
    n2 = len(total_ret_rows)

    ax2 = fig.add_axes([0.555, 0.115, 0.43, 0.695])
    ax2.set_facecolor(BG)
    for sp in ['top', 'right', 'left']: ax2.spines[sp].set_visible(False)
    ax2.spines['bottom'].set_color(BORDER)
    ax2.tick_params(left=False)

    ys2 = np.arange(n2)
    bar_h2 = 0.52

    div_rets   = [r[2] for r in total_ret_rows]
    cap_rets   = [r[3] for r in total_ret_rows]
    total_rets = [r[1] for r in total_ret_rows]

    for i, (d, c, tot) in enumerate(zip(div_rets, cap_rets, total_rets)):
        y = ys2[i]
        # Dividend segment (always ≥0, right from 0)
        ax2.barh(y, d, height=bar_h2, color=BLUE2, zorder=3)
        if c >= 0:
            # Capital gain: stacked right of dividend
            ax2.barh(y, c, height=bar_h2, left=d, color=TEAL, zorder=3)
        else:
            # Capital loss: extends left from 0 (overlaps the dividend bar)
            ax2.barh(y, c, height=bar_h2, left=0, color=NEG, alpha=0.75, zorder=4)
        # Total label
        label_x = (d + max(c, 0)) + 2
        col = POS if tot >= 0 else NEG
        ax2.text(label_x, y, f'{tot:.0f}%',
                 va='center', fontsize=8, color=col,
                 fontproperties=jf(8, True))

    ax2.set_yticks(ys2)
    ax2.set_yticklabels([f'{sname(r[0])} [{r[0]}]' for r in total_ret_rows],
                        fontsize=8, color=TEXT, fontproperties=jf(8))
    ax2.set_xlabel('取得コスト対比リターン（%）', fontsize=8, color=TEXT2, fontproperties=jf(8))
    ax2.set_ylim(-0.8, n2 - 0.2)
    ax2.invert_yaxis()
    x_max = max(total_rets) * 1.18 + 15
    x_min = min(min(r for r in cap_rets if r < 0), 0) * 1.1 if any(r < 0 for r in cap_rets) else -5
    ax2.set_xlim(x_min, x_max)
    ax2.axvline(0,   color=TEXT2,  linewidth=0.8, zorder=2)
    ax2.axvline(100, color=BORDER, linewidth=0.8, linestyle='--', alpha=0.7, zorder=2)
    ax2.text(101, -0.65, '100%', fontsize=6.5, color=TEXT2, fontproperties=jf(6.5))
    ax2.tick_params(axis='x', colors=TEXT2, labelsize=7)
    ax2.grid(axis='x', color=BORDER, linewidth=0.4, alpha=0.7, zorder=1)
    ax2.set_title('（受取配当累計＋税抜売却益）÷ 取得コスト', fontsize=9, color=TEXT,
                  fontproperties=jf(9, True), pad=6)

    # Combined legend
    leg_ax = fig.add_axes([0.01, 0.075, 0.98, 0.040])
    leg_ax.axis('off'); leg_ax.set_facecolor(BG)
    handles = [
        mpatches.Patch(facecolor=BLUE2,  label='現在利回り（現在株価ベース）'),
        mpatches.Patch(facecolor=POS,    label='コスト利回り 3%以上'),
        mpatches.Patch(facecolor=AMBER,  label='コスト利回り 2〜3%'),
        mpatches.Patch(facecolor=TEXT2,  label='コスト利回り 2%未満'),
        mpatches.Patch(facecolor=BLUE2,  label='配当累計 / 取得コスト'),
        mpatches.Patch(facecolor=TEAL,   label='税抜売却益 / 取得コスト（利益）'),
        mpatches.Patch(facecolor=NEG,    label='税抜売却益 / 取得コスト（損失）'),
    ]
    leg_ax.legend(handles=handles, loc='center', ncol=4, frameon=False,
                  fontsize=7, prop=jf(7))

    dark_footer(fig, '個人資産管理  |  配当分析レポート', 3, 3)
    return fig_to_img(fig)

# ─── Compose PDF ─────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = f'{OUT_DIR}/dividend_analysis_v1.pdf'

    print('Generating page 1: small multiples…')
    img1 = page_small_multiples()
    print('Generating page 2: heatmap…')
    img2 = page_heatmap()
    print('Generating page 3: yield ranking…')
    img3 = page_yield_ranking()

    imgs = [img1, img2, img3]
    rgb  = [im.convert('RGB') for im in imgs]
    rgb[0].save(out_path, save_all=True, append_images=rgb[1:])
    size_kb = os.path.getsize(out_path) // 1024
    print(f'Done → {out_path}  ({size_kb} KB)')

if __name__ == '__main__':
    main()
