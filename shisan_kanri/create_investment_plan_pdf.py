#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import warnings, io, os
warnings.filterwarnings('ignore')

# ─── フォント設定 ────────────────────────────────────────────────────────────
import matplotlib.font_manager as fm
available = [f.name for f in fm.fontManager.ttflist]
JP_FONT = next(
    (f for f in ['Hiragino Sans','Hiragino Kaku Gothic ProN','Hiragino Kaku Gothic Pro',
                 'Yu Gothic','Noto Sans CJK JP','IPAexGothic']
     if f in available), None)
if JP_FONT:
    plt.rcParams['font.family'] = JP_FONT
plt.rcParams['axes.unicode_minus'] = False

# ─── カラー ──────────────────────────────────────────────────────────────────
NAVY   = '#1E3A5F'
BLUE   = '#2E86C1'
LIGHT  = '#D6EAF8'
GREEN  = '#1E8B4C'
RED    = '#C0392B'
GRAY   = '#585858'
WHITE  = '#FFFFFF'
GOLD   = '#F39C12'
PURPLE = '#8E44AD'
ORANGE = '#E67E22'
TEAL   = '#17808B'
BG     = '#F8FBFF'
BG2    = '#F0F7F0'
BG3    = '#FFF8F0'
BG4    = '#F8F0FF'
BG5    = '#F0F8FF'

# ─── ポートフォリオデータ ─────────────────────────────────────────────────────
TOTAL_ASSET  = 50847524   # 約5084万円
TOTAL_PROFIT = 20544980   # 約2054万円
TOTAL_COST   = TOTAL_ASSET - TOTAL_PROFIT

# ─── ユーティリティ ─────────────────────────────────────────────────────────

def new_fig(title="", subtitle="", title_color=NAVY, accent=GOLD):
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=BG)
    if title:
        ax_h = fig.add_axes([0, 0.88, 1, 0.12])
        ax_h.set_facecolor(title_color); ax_h.axis('off')
        ax_h.set_xlim(0,1); ax_h.set_ylim(0,1)
        ax_h.text(0.025, 0.64, title, color=WHITE, fontsize=20,
                  fontweight='bold', va='center')
        if subtitle:
            ax_h.text(0.025, 0.18, subtitle, color='#AACCEE', fontsize=9, va='center')
        ax_h.axhline(0, color=accent, linewidth=3)
    return fig


def info_box(ax, x, y, w, h, label, value, bg, border, val_color=NAVY, note=""):
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015",
                          linewidth=1.8, edgecolor=border, facecolor=bg,
                          transform=ax.transAxes)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h*0.78, label, ha='center', fontsize=8.5,
            color=GRAY, transform=ax.transAxes)
    ax.text(x + w/2, y + h*0.40, value, ha='center', fontsize=13,
            fontweight='bold', color=val_color, transform=ax.transAxes)
    if note:
        ax.text(x + w/2, y + h*0.10, note, ha='center', fontsize=7.5,
                color=GRAY, transform=ax.transAxes)


def save_pil(fig):
    from PIL import Image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).convert('RGB')
    plt.close(fig)
    return img


# ════════════════════════════════════════════════════════════════════════════
# スライド 1: 表紙
# ════════════════════════════════════════════════════════════════════════════

def slide_cover():
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=NAVY)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_facecolor(NAVY)

    # 背景装飾
    for i, (x, y, r, alpha) in enumerate([
        (0.85,0.85,0.25,0.06),(0.1,0.1,0.2,0.05),(0.9,0.15,0.15,0.05)]):
        circle = plt.Circle((x, y), r, color=BLUE, alpha=alpha, transform=ax.transAxes)
        ax.add_patch(circle)

    ax.axhline(0.46, color=GOLD, linewidth=4, xmin=0.05, xmax=0.95)

    ax.text(0.5, 0.83, "投資プラン提案レポート", ha='center', color=WHITE,
            fontsize=30, fontweight='bold')
    ax.text(0.5, 0.70, "市場分析 & ポートフォリオ戦略", ha='center', color=GOLD,
            fontsize=20, fontweight='bold')
    ax.text(0.5, 0.59, "2026年6月19日  現在の市場状況・世界情勢・為替を総合判断", ha='center',
            color='#AACCEE', fontsize=12)

    # 4つのキーワードカード
    items = [
        ("日経平均", "64,024円\n（最高値圏）",      BLUE),
        ("ドル/円",  "159円台後半\n（円安継続）",    ORANGE),
        ("日銀政策金利", "1.0%\n（31年ぶり高水準）", RED),
        ("地政学リスク", "中東情勢\n（警戒継続）",   PURPLE),
    ]
    for i, (lbl, val, clr) in enumerate(items):
        x = 0.07 + i * 0.23
        rect = FancyBboxPatch((x, 0.22), 0.20, 0.17,
                              boxstyle="round,pad=0.01", linewidth=2,
                              edgecolor=clr, facecolor='#1A3050',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x+0.10, 0.365, lbl, ha='center', color='#AACCEE',
                fontsize=8.5, transform=ax.transAxes)
        ax.text(x+0.10, 0.275, val, ha='center', color=clr,
                fontsize=10, fontweight='bold', transform=ax.transAxes)

    ax.text(0.5, 0.10, "プランA: 守り重視型  /  プランB: 積み立て継続型  /  プランC: 攻め型成長株  /  プランD: 円高対応型",
            ha='center', color='#6688AA', fontsize=10)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# スライド 2: 現在の市場環境サマリー
# ════════════════════════════════════════════════════════════════════════════

def slide_market_summary():
    fig = new_fig("現在の市場環境サマリー（2026年6月）",
                  "日経平均：64,024円（最高値圏から急落）  |  S&P500年末目標7,900  |  ドル円159円台後半")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # ─ 左カラム：株式市場 ─
    # 日本株
    rect = FancyBboxPatch((0.02,0.54), 0.46, 0.31, boxstyle="round,pad=0.015",
                          lw=2, edgecolor=BLUE, facecolor='#EEF5FF', transform=ax.transAxes)
    ax.add_patch(rect)
    ax.text(0.25, 0.83, "日本株式市場", ha='center', fontsize=13,
            fontweight='bold', color=BLUE, transform=ax.transAxes)
    jp_items = [
        ("日経平均（6/8）",    "64,024円  前週比 -3.85%"),
        ("年初来高値（6/1）",  "66,900円台（史上最高値更新）"),
        ("野村証券 年末目標",  "68,000円（AI・半導体好業績）"),
        ("注目セクター",       "AI/半導体・商社・金融・通信"),
    ]
    for i, (k, v) in enumerate(jp_items):
        y = 0.78 - i*0.057
        ax.text(0.04, y, f"■ {k}", fontsize=8.5, fontweight='bold',
                color=NAVY, transform=ax.transAxes)
        ax.text(0.22, y, v, fontsize=8.5, color=GRAY, transform=ax.transAxes)

    # 米国株
    rect2 = FancyBboxPatch((0.02,0.20), 0.46, 0.31, boxstyle="round,pad=0.015",
                           lw=2, edgecolor=ORANGE, facecolor='#FFF5EE', transform=ax.transAxes)
    ax.add_patch(rect2)
    ax.text(0.25, 0.49, "米国株式市場", ha='center', fontsize=13,
            fontweight='bold', color=ORANGE, transform=ax.transAxes)
    us_items = [
        ("S&P500 2026年末目標", "野村7,900 / シティ8,100 / 平均7,450"),
        ("企業業績成長率",       "+22.8%（2026年通年見込み）"),
        ("利上げ観測",           "年内は据え置き→後半0.5%利下げ"),
        ("注目テーマ",           "AI・データセンター・クラウド"),
    ]
    for i, (k, v) in enumerate(us_items):
        y = 0.44 - i*0.057
        ax.text(0.04, y, f"■ {k}", fontsize=8.5, fontweight='bold',
                color='#C05000', transform=ax.transAxes)
        ax.text(0.27, y, v, fontsize=8.5, color=GRAY, transform=ax.transAxes)

    # ─ 右カラム：金利・為替・リスク ─
    rect3 = FancyBboxPatch((0.52,0.54), 0.46, 0.31, boxstyle="round,pad=0.015",
                           lw=2, edgecolor=RED, facecolor='#FFF0EE', transform=ax.transAxes)
    ax.add_patch(rect3)
    ax.text(0.75, 0.83, "金利環境", ha='center', fontsize=13,
            fontweight='bold', color=RED, transform=ax.transAxes)
    rate_items = [
        ("日銀政策金利（6/16）", "1.00%（0.75%→1.0%利上げ）"),
        ("日銀 次回利上げ予想",  "2026年12月・2027年6月"),
        ("FRB 政策金利",        "据え置き（年後半0.5%利下げ予想）"),
        ("米国インフレ（PCE）",  "2.4%（徐々に鈍化方向）"),
    ]
    for i, (k, v) in enumerate(rate_items):
        y = 0.78 - i*0.057
        ax.text(0.54, y, f"■ {k}", fontsize=8.5, fontweight='bold',
                color=RED, transform=ax.transAxes)
        ax.text(0.745, y, v, fontsize=8.5, color=GRAY, transform=ax.transAxes)

    rect4 = FancyBboxPatch((0.52,0.20), 0.46, 0.31, boxstyle="round,pad=0.015",
                           lw=2, edgecolor=PURPLE, facecolor='#F5EEFF', transform=ax.transAxes)
    ax.add_patch(rect4)
    ax.text(0.75, 0.49, "為替・地政学リスク", ha='center', fontsize=13,
            fontweight='bold', color=PURPLE, transform=ax.transAxes)
    risk_items = [
        ("ドル円（6月初旬）",    "159円台後半（介入警戒感）"),
        ("2026年末 円高予想",    "野村152円 / 三井住友150円"),
        ("中東情勢",             "イスラエル・イラン衝突継続"),
        ("ホルムズ海峡",         "通航制限→原油高・物流混乱"),
    ]
    for i, (k, v) in enumerate(risk_items):
        y = 0.44 - i*0.057
        ax.text(0.54, y, f"■ {k}", fontsize=8.5, fontweight='bold',
                color=PURPLE, transform=ax.transAxes)
        ax.text(0.73, y, v, fontsize=8.5, color=GRAY, transform=ax.transAxes)

    # 下部サマリーバー
    rect5 = FancyBboxPatch((0.02,0.03), 0.96, 0.14, boxstyle="round,pad=0.01",
                           lw=0, facecolor='#1E3A5F', transform=ax.transAxes)
    ax.add_patch(rect5)
    ax.text(0.5, 0.09, "総評：日本株最高値圏・米国株高値更新モード一方、日銀利上げ継続・円高圧力・中東リスクの3点が潜在的逆風。守りと攻めのバランスが重要な局面。",
            ha='center', va='center', fontsize=9.5, color=WHITE,
            fontweight='bold', transform=ax.transAxes)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# スライド 3: 現ポートフォリオの強み・課題
# ════════════════════════════════════════════════════════════════════════════

def slide_portfolio_analysis():
    fig = new_fig("現ポートフォリオの強み・課題分析",
                  f"総評価額: {TOTAL_ASSET/1e8:.2f}億円  |  総含み益: +{TOTAL_PROFIT/1e4:.0f}万円  |  損益率: +{TOTAL_PROFIT/TOTAL_COST*100:.1f}%")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # 強み（左）
    ax.text(0.25, 0.86, "強み（現状維持の根拠）", ha='center', fontsize=14,
            fontweight='bold', color=GREEN, transform=ax.transAxes)
    strengths = [
        ("高い分散性",
         "日本株28銘柄・米国株7銘柄・投信・国債\n地域・セクター・商品タイプを網羅"),
        ("大幅な含み益",
         "総損益率+68%。SKYT+578%、三井物産\n+239%など圧倒的な含み益バッファー"),
        ("高配当ポートフォリオ",
         "NTT・KDDI・オリックス・HDV・SPYDなど\n安定したインカムゲイン確保"),
        ("NISA非課税活用",
         "成長投資枠・つみたて枠・旧NISAをフル活用\n含み益に対する税負担なし"),
        ("国債によるリスク分散",
         "米国国債4本（2027〜2053年満期）\n株式急落時の安全バッファー"),
    ]
    for i, (title, desc) in enumerate(strengths):
        y = 0.75 - i*0.135
        rect = FancyBboxPatch((0.02, y-0.02), 0.44, 0.115,
                              boxstyle="round,pad=0.01", lw=1.5,
                              edgecolor=GREEN, facecolor='#F0FFF4',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(0.04, y+0.06, f"✓  {title}", fontsize=10,
                fontweight='bold', color=GREEN, transform=ax.transAxes)
        ax.text(0.065, y+0.005, desc, fontsize=8.5, color=GRAY,
                transform=ax.transAxes)

    # 課題（右）
    ax.text(0.75, 0.86, "課題・リスク（対応すべき点）", ha='center', fontsize=14,
            fontweight='bold', color=RED, transform=ax.transAxes)
    challenges = [
        ("円安依存リスク",
         "米国資産比率54%超。円高転換（150円台）\nで円換算評価額が大幅減少する可能性"),
        ("高値圏での集中リスク",
         "日経平均・S&P500とも高値圏。\n地政学リスク悪化で急落シナリオあり"),
        ("日銀利上げの影響",
         "政策金利1.0%到達。追加利上げで\nNTT・KDDI等の高配当株に逆風の可能性"),
        ("エネルギー価格リスク",
         "中東情勢悪化・ホルムズ海峡閉鎖で\n原油高→日本株全体に逆風"),
        ("債券の機会コスト",
         "米国国債717万円。日銀利上げ局面では\n円建て高金利商品への移行も選択肢"),
    ]
    for i, (title, desc) in enumerate(challenges):
        y = 0.75 - i*0.135
        rect = FancyBboxPatch((0.52, y-0.02), 0.44, 0.115,
                              boxstyle="round,pad=0.01", lw=1.5,
                              edgecolor=RED, facecolor='#FFF5F5',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(0.54, y+0.06, f"!  {title}", fontsize=10,
                fontweight='bold', color=RED, transform=ax.transAxes)
        ax.text(0.555, y+0.005, desc, fontsize=8.5, color=GRAY,
                transform=ax.transAxes)

    # 下部: 結論
    rect_b = FancyBboxPatch((0.02,0.02), 0.96, 0.07,
                            boxstyle="round,pad=0.01", lw=0,
                            facecolor=NAVY, transform=ax.transAxes)
    ax.add_patch(rect_b)
    ax.text(0.5, 0.055, "結論：含み益バッファーは十分。円高・利上げ・地政学の3リスクへの対応が次のアクションポイント。",
            ha='center', fontsize=10, fontweight='bold', color=GOLD,
            transform=ax.transAxes)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# スライド 4: プランA（守り重視・利益確定型）
# ════════════════════════════════════════════════════════════════════════════

def slide_plan_a():
    fig = new_fig("プランA：守り重視・利益確定型", title_color='#145A32', accent=GREEN,
                  subtitle="推奨対象：円高・株安リスクを優先したい方 / リスク許容度：低〜中")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # ラベルバー
    rect_lbl = FancyBboxPatch((0.02,0.83), 0.96, 0.04, boxstyle="round,pad=0.005",
                              lw=0, facecolor='#D5F5E3', transform=ax.transAxes)
    ax.add_patch(rect_lbl)
    ax.text(0.5, 0.852, "戦略の核心：大幅含み益銘柄を一部利益確定し、現金・円建て安全資産比率を引き上げる",
            ha='center', fontsize=10, fontweight='bold', color='#145A32',
            transform=ax.transAxes)

    # 左: アクション表
    ax.text(0.02, 0.80, "推奨アクション", fontsize=13, fontweight='bold',
            color='#145A32', transform=ax.transAxes)
    actions = [
        ("SELL",  GREEN,    "三井物産（8031）",    "200株売却",   "含み益+143万 確定。+239%の利益確定タイミングとして適切"),
        ("SELL",  GREEN,    "SKYT（旧NISA）",      "200株売却",   "旧NISA口座・+578%。一部確定で利益を守る（残250株継続）"),
        ("SELL",  GREEN,    "VTI（特定預り）",      "80株売却",    "最大保有ポジション。円高前に一部ドルを円転（残100株継続）"),
        ("SELL",  GREEN,    "オリックス（8591）",   "69株売却",    "+67%の含み益の半分を確定。配当取り後の利確戦略"),
        ("BUY",   BLUE,     "個人向け国債（変動型）","100〜200万円", "日銀利上げ局面で利回りが上昇。元本保証で安全"),
        ("BUY",   BLUE,     "MRF/MMF",              "売却代金の半分", "当面の待機資金として保有。次の投資タイミングに備える"),
    ]
    headers = ["操作", "銘柄・商品", "数量・金額", "理由"]
    col_xs  = [0.02, 0.09, 0.27, 0.40, 0.97]
    col_ws  = [0.06, 0.17, 0.12, 0.57]

    # ヘッダー
    for j, (hdr, cx, cw) in enumerate(zip(headers, col_xs, col_ws)):
        rect = FancyBboxPatch((cx, 0.73), cw-0.005, 0.04,
                              boxstyle="round,pad=0.002", lw=0,
                              facecolor='#145A32', transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(cx+cw/2, 0.752, hdr, ha='center', fontsize=9,
                fontweight='bold', color=WHITE, transform=ax.transAxes)

    for i, (op, clr, name, qty, reason) in enumerate(actions):
        bg = '#F0FFF4' if i%2==0 else WHITE
        ry = 0.685 - i*0.072
        row_data = [op, name, qty, reason]
        for j, (val, cx, cw) in enumerate(zip(row_data, col_xs, col_ws)):
            rect = FancyBboxPatch((cx, ry), cw-0.005, 0.063,
                                  boxstyle="round,pad=0.002", lw=0.5,
                                  edgecolor='#CCE5CC', facecolor=bg,
                                  transform=ax.transAxes)
            ax.add_patch(rect)
            vc = GREEN if op=='SELL' else BLUE
            fw = 'bold' if j==0 else 'normal'
            ax.text(cx+cw/2, ry+0.031, val, ha='center', va='center',
                    fontsize=8.5, color=(vc if j==0 else NAVY), fontweight=fw,
                    transform=ax.transAxes)

    # 右: アセット配分変化
    ax.text(0.52, 0.80, "実施後のアセット配分イメージ", fontsize=12, fontweight='bold',
            color='#145A32', transform=ax.transAxes)

    ax2 = fig.add_axes([0.52, 0.24, 0.44, 0.54])
    # 現在
    current = [30.2, 15.0, 40.6, 14.1]   # 日本株・投信・米国株+債券・現金
    after   = [26.0, 15.0, 33.0, 26.0]
    labels  = ['日本株', '投資信託', '米国株\n+国債', '現金・\n安全資産']
    x = np.arange(len(labels))
    w = 0.35
    bars1 = ax2.bar(x-w/2, current, w, label='現在', color=['#2E86C1','#1E8B4C','#E67E22','#BDC3C7'],
                    edgecolor='white', alpha=0.7)
    bars2 = ax2.bar(x+w/2, after,   w, label='実施後', color=['#2E86C1','#1E8B4C','#E67E22','#95A5A6'],
                    edgecolor='white')
    ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel('%', fontsize=9); ax2.set_ylim(0, 45)
    ax2.set_title('配分変化（資産比率%）', fontsize=11, fontweight='bold')
    ax2.legend(fontsize=9); ax2.grid(axis='y', alpha=0.3)
    ax2.spines[['top','right']].set_visible(False)
    for bar in bars2:
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                 f'{bar.get_height():.0f}%', ha='center', fontsize=8, fontweight='bold')

    # 下部ポイント
    rect_b = FancyBboxPatch((0.02,0.02), 0.96, 0.10,
                            boxstyle="round,pad=0.01", lw=0, facecolor='#145A32',
                            transform=ax.transAxes)
    ax.add_patch(rect_b)
    points = ["円高進行時に米国資産の円換算損失をヘッジ",
              "高値圏での利益確定で下落リスクを軽減",
              "個人向け国債で日銀利上げの恩恵を享受"]
    for i, pt in enumerate(points):
        ax.text(0.04 + i*0.33, 0.095, f"✓ {pt}", fontsize=9.5,
                color=WHITE, fontweight='bold', transform=ax.transAxes)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# スライド 5: プランB（積み立て継続・現状維持型）
# ════════════════════════════════════════════════════════════════════════════

def slide_plan_b():
    fig = new_fig("プランB：積み立て継続・現状維持型", title_color=BLUE, accent=GOLD,
                  subtitle="推奨対象：長期・安定運用重視の方 / リスク許容度：中")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # バナー
    rect_lbl = FancyBboxPatch((0.02,0.83), 0.96, 0.04, boxstyle="round,pad=0.005",
                              lw=0, facecolor='#D6EAF8', transform=ax.transAxes)
    ax.add_patch(rect_lbl)
    ax.text(0.5, 0.852, "戦略の核心：現ポートフォリオの高い含み益・分散性を活かし、積み立てと再投資を継続",
            ha='center', fontsize=10, fontweight='bold', color=BLUE, transform=ax.transAxes)

    # アクション（左）
    ax.text(0.02, 0.80, "推奨アクション", fontsize=13, fontweight='bold',
            color=BLUE, transform=ax.transAxes)
    b_actions = [
        ("HOLD", GRAY,   "全ポジション継続保有",    "大幅含み益あり。長期ホールドが基本"),
        ("ADD",  BLUE,   "eMAXIS Slim オールカントリー\nつみたて枠の積立増額",
         "月3〜5万円→月7〜10万円に増額\n（年間つみたて枠120万を最大活用）"),
        ("ADD",  BLUE,   "eMAXIS Slim オールカントリー\nNISA成長投資枠も追加投資",
         "年間240万円の成長投資枠を活用\n相場下落時は追加購入チャンス"),
        ("DRIP", GREEN,  "配当金・分配金の再投資",  "NTT・KDDI・オリックス等の配当を\n都度、投信や高配当ETFに再投資"),
        ("HOLD", GRAY,   "米国債4本は満期まで保有", "満期分散（2027〜2053年）を維持\n金利収入を積み上げる"),
    ]

    for i, (op, clr, name, reason) in enumerate(b_actions):
        y = 0.72 - i*0.12
        rect = FancyBboxPatch((0.02, y), 0.46, 0.10,
                              boxstyle="round,pad=0.01", lw=1.5,
                              edgecolor=clr, facecolor='#F0F8FF',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        op_bg = FancyBboxPatch((0.03, y+0.03), 0.055, 0.04,
                               boxstyle="round,pad=0.005", lw=0,
                               facecolor=clr, transform=ax.transAxes)
        ax.add_patch(op_bg)
        ax.text(0.057, y+0.053, op, ha='center', va='center', fontsize=8,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
        ax.text(0.10, y+0.072, name, fontsize=9, fontweight='bold',
                color=NAVY, transform=ax.transAxes)
        ax.text(0.10, y+0.022, reason, fontsize=8, color=GRAY,
                transform=ax.transAxes)

    # 積み立てシミュレーション（右）
    ax.text(0.52, 0.80, "積み立て継続シミュレーション", fontsize=12,
            fontweight='bold', color=BLUE, transform=ax.transAxes)

    ax2 = fig.add_axes([0.52, 0.30, 0.45, 0.48])
    years = np.arange(0, 11)
    # 現在5084万円から月10万積立、年率6%成長
    base = 50847524
    tsumitate = 10 * 12 * 10000  # 月10万
    vals_grow = [base * (1.06**y) + tsumitate * ((1.06**y - 1) / 0.06) for y in years]
    vals_flat = [base + tsumitate * y for y in years]  # 積立のみ(増加なし)
    ax2.fill_between(years, [v/1e8 for v in vals_flat], [v/1e8 for v in vals_grow],
                     alpha=0.25, color=BLUE, label='運用益（年率6%想定）')
    ax2.plot(years, [v/1e8 for v in vals_flat], 'o--', color=GRAY,
             linewidth=1.5, markersize=5, label='積立のみ（利回り0%）')
    ax2.plot(years, [v/1e8 for v in vals_grow], 'o-', color=BLUE,
             linewidth=2.5, markersize=7, label='積立継続（年率6%）')
    ax2.set_xlabel('経過年数', fontsize=10)
    ax2.set_ylabel('評価額（億円）', fontsize=10)
    ax2.set_title('月10万積立・年率6%想定の資産推移', fontsize=11, fontweight='bold')
    ax2.legend(fontsize=9); ax2.grid(alpha=0.35)
    ax2.spines[['top','right']].set_visible(False)
    ax2.text(10.1, vals_grow[-1]/1e8, f'{vals_grow[-1]/1e8:.1f}億', fontsize=9,
             fontweight='bold', color=BLUE, va='center')

    # 下部
    rect_b = FancyBboxPatch((0.02,0.02), 0.96, 0.10, boxstyle="round,pad=0.01",
                            lw=0, facecolor=BLUE, transform=ax.transAxes)
    ax.add_patch(rect_b)
    points = ["長期積立で時間分散・コスト平均化を実現",
              "NISA年間360万円の非課税枠をフル活用",
              "配当再投資で複利効果を最大化"]
    for i, pt in enumerate(points):
        ax.text(0.04+i*0.33, 0.095, f"✓ {pt}", fontsize=9.5,
                color=WHITE, fontweight='bold', transform=ax.transAxes)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# スライド 6: プランC（攻め型・成長株追加）
# ════════════════════════════════════════════════════════════════════════════

def slide_plan_c():
    fig = new_fig("プランC：攻め型・成長株追加型", title_color='#6C3483', accent=GOLD,
                  subtitle="推奨対象：高リターンを狙う方 / リスク許容度：高 ※現在の含み益バッファーが前提")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    rect_lbl = FancyBboxPatch((0.02,0.83), 0.96, 0.04, boxstyle="round,pad=0.005",
                              lw=0, facecolor='#E8DAEF', transform=ax.transAxes)
    ax.add_patch(rect_lbl)
    ax.text(0.5, 0.852, "戦略の核心：AI・半導体・ロボティクスなど次世代テーマへの集中投資で高リターンを狙う",
            ha='center', fontsize=10, fontweight='bold', color=PURPLE, transform=ax.transAxes)

    # 追加候補銘柄（左）
    ax.text(0.02, 0.80, "追加候補銘柄・テーマ", fontsize=13, fontweight='bold',
            color=PURPLE, transform=ax.transAxes)
    candidates = [
        ("米国株", "#6C3483", [
            ("NVDA  エヌビディア",         "AI半導体の絶対的リーダー。データセンター需要拡大"),
            ("TSMC  台湾セミコン",         "AI・次世代スマホ向け最先端半導体製造"),
            ("MSFT  マイクロソフト",       "Azure AI・Copilot。クラウドAI展開で継続成長"),
        ]),
        ("日本株", BLUE, [
            ("6857  アドバンテスト",       "半導体テスト機器。AIチップ増産の恩恵直撃"),
            ("6920  レーザーテック",       "EUV露光機向け検査装置。国内随一の半導体関連"),
            ("6702  富士通",               "AIシステムインテグレーション。国内AI需要を取込"),
        ]),
    ]
    y_base = 0.73
    for market, clr, stocks in candidates:
        rect_h = FancyBboxPatch((0.02, y_base), 0.46, 0.04, boxstyle="round,pad=0.003",
                                lw=0, facecolor=clr, transform=ax.transAxes)
        ax.add_patch(rect_h)
        ax.text(0.25, y_base+0.022, market, ha='center', fontsize=10,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
        for i, (ticker, desc) in enumerate(stocks):
            y = y_base - 0.035 - i*0.07
            rect_s = FancyBboxPatch((0.02, y), 0.46, 0.062,
                                    boxstyle="round,pad=0.005", lw=1,
                                    edgecolor=clr, facecolor='#FAF0FF',
                                    transform=ax.transAxes)
            ax.add_patch(rect_s)
            ax.text(0.04, y+0.04, ticker, fontsize=9.5, fontweight='bold',
                    color=clr, transform=ax.transAxes)
            ax.text(0.04, y+0.01, desc, fontsize=8.5, color=GRAY,
                    transform=ax.transAxes)
        y_base -= 0.035 + len(stocks)*0.07 + 0.02

    # 右：テーマ別期待リターン比較
    ax.text(0.52, 0.80, "テーマ別 期待リターン比較（3〜5年）", fontsize=12,
            fontweight='bold', color=PURPLE, transform=ax.transAxes)

    ax2 = fig.add_axes([0.52, 0.29, 0.45, 0.49])
    themes = ['AI・半導体\n（NVDA等）', '高配当株\n（NTT等）', 'インデックス\n（VTI等）',
              'J-REIT', '個人向け\n国債']
    exp_ret = [28, 6, 10, 4, 1.5]
    exp_risk= [45, 12, 18, 15, 0]
    colors_c = [PURPLE, BLUE, ORANGE, TEAL, GREEN]
    for i, (theme, ret, risk, clr) in enumerate(zip(themes, exp_ret, exp_risk, colors_c)):
        ax2.scatter(risk, ret, s=220, color=clr, zorder=5, edgecolors='white', linewidth=1.5)
        ax2.annotate(theme, (risk, ret), textcoords="offset points",
                     xytext=(8,2), fontsize=8, color=clr)
    ax2.set_xlabel('リスク（ボラティリティ想定%）', fontsize=9)
    ax2.set_ylabel('期待リターン（年率%）', fontsize=9)
    ax2.set_title('リスク・リターン マップ', fontsize=11, fontweight='bold')
    ax2.grid(alpha=0.35); ax2.spines[['top','right']].set_visible(False)
    ax2.set_xlim(-3, 55); ax2.set_ylim(-2, 36)
    ax2.axvline(15, color=RED, linewidth=0.8, linestyle='--', alpha=0.5)
    ax2.axhline(10, color=RED, linewidth=0.8, linestyle='--', alpha=0.5)
    ax2.text(15.5, 1, 'リスク中央値', fontsize=7, color=RED, alpha=0.7)

    # 注意事項
    rect_warn = FancyBboxPatch((0.52, 0.22), 0.45, 0.05, boxstyle="round,pad=0.01",
                               lw=1.5, edgecolor=RED, facecolor='#FFF0F0',
                               transform=ax.transAxes)
    ax.add_patch(rect_warn)
    ax.text(0.745, 0.247, "! 高リスク銘柄への追加投資は、既存の含み益をバッファーとして損失リスクを認識の上で行うこと",
            ha='center', fontsize=8, color=RED, transform=ax.transAxes)

    # 下部
    rect_b = FancyBboxPatch((0.02,0.02), 0.96, 0.10, boxstyle="round,pad=0.01",
                            lw=0, facecolor='#6C3483', transform=ax.transAxes)
    ax.add_patch(rect_b)
    points = ["NISA成長投資枠を活用し非課税で成長株保有",
              "既存含み益+68%がリスク緩衝材",
              "分散投資の原則は維持（1銘柄≦5%）"]
    for i, pt in enumerate(points):
        ax.text(0.04+i*0.33, 0.095, f"✓ {pt}", fontsize=9.5,
                color=WHITE, fontweight='bold', transform=ax.transAxes)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# スライド 7: プランD（円高対応・国内回帰型）
# ════════════════════════════════════════════════════════════════════════════

def slide_plan_d():
    fig = new_fig("プランD：円高対応・国内回帰型", title_color='#784212', accent=ORANGE,
                  subtitle="推奨対象：円高シナリオに備えたい方 / リスク許容度：低〜中")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    rect_lbl = FancyBboxPatch((0.02,0.83), 0.96, 0.04, boxstyle="round,pad=0.005",
                              lw=0, facecolor='#FAD7A0', transform=ax.transAxes)
    ax.add_patch(rect_lbl)
    ax.text(0.5, 0.852, "戦略の核心：円高進行（150〜146円台）シナリオを想定。米国資産を段階的に円建て資産へシフト",
            ha='center', fontsize=10, fontweight='bold', color='#784212', transform=ax.transAxes)

    # 左：アクション
    ax.text(0.02, 0.80, "推奨アクション", fontsize=13, fontweight='bold',
            color='#784212', transform=ax.transAxes)

    d_actions = [
        ("SELL", RED,     "VTI（特定口座）段階売却",
         "円高が進む前に80〜100株を売却。159円→150円の変動だけで\n6%の為替損失（約645万円相当）を回避できる"),
        ("SELL", RED,     "AMBQ（特定）全売却検討",
         "小型米国個別株。取得比+178%。ドル高恩恵が終わる前に\n利益確定し、円建て資産に置き換え"),
        ("BUY",  ORANGE,  "国内高配当株の追加",
         "三菱UFJ・東京海上・NTTなど日銀利上げメリット銘柄を追加。\n円高でも影響を受けにくい内需・金融株"),
        ("BUY",  ORANGE,  "J-REIT（不動産投資信託）",
         "国内インフレ局面で実物資産が上昇。リート価格の底打ちを\n確認後、NISAで10〜20万円から打診買い"),
        ("CONVERT",GREEN, "米ドル建て債券の一部円転",
         "2027年満期のMF164（約205万円）を満期後に円建て\n個人向け国債(変動型)へロールオーバー検討"),
    ]

    for i, (op, clr, name, reason) in enumerate(d_actions):
        y = 0.72 - i*0.12
        rect = FancyBboxPatch((0.02, y), 0.46, 0.10,
                              boxstyle="round,pad=0.01", lw=1.5,
                              edgecolor=clr, facecolor='#FFF8F0',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        op_bg = FancyBboxPatch((0.03, y+0.03), 0.07, 0.04,
                               boxstyle="round,pad=0.005", lw=0,
                               facecolor=clr, transform=ax.transAxes)
        ax.add_patch(op_bg)
        ax.text(0.065, y+0.053, op, ha='center', va='center', fontsize=7.5,
                fontweight='bold', color=WHITE, transform=ax.transAxes)
        ax.text(0.115, y+0.072, name, fontsize=9.5, fontweight='bold',
                color=NAVY, transform=ax.transAxes)
        ax.text(0.115, y+0.012, reason, fontsize=7.5, color=GRAY,
                transform=ax.transAxes)

    # 右：円高シナリオ影響シミュレーション
    ax.text(0.52, 0.80, "円高シナリオ 影響シミュレーション", fontsize=12,
            fontweight='bold', color='#784212', transform=ax.transAxes)

    ax2 = fig.add_axes([0.52, 0.32, 0.45, 0.46])
    fx_rates  = [159, 155, 152, 150, 146, 140]
    us_assets_jpy = 27840364  # 現在の米国資産合計（円換算）

    # 現在159円基準で試算
    base_rate = 159
    vals = [us_assets_jpy * (r / base_rate) / 1e4 for r in fx_rates]
    diff = [v - us_assets_jpy/1e4 for v in vals]

    color_bars = [GREEN if d >= 0 else RED for d in diff]
    bars = ax2.bar(range(len(fx_rates)), diff, color=color_bars,
                   edgecolor='white', linewidth=1, width=0.65)
    ax2.set_xticks(range(len(fx_rates)))
    ax2.set_xticklabels([f'{r}円' for r in fx_rates], fontsize=9)
    ax2.set_ylabel('円換算増減（万円）', fontsize=9)
    ax2.set_title('為替変動による米国資産の増減\n（米国資産2,784万円ベース）', fontsize=10, fontweight='bold')
    ax2.axhline(0, color=GRAY, linewidth=0.8)
    ax2.grid(axis='y', alpha=0.35); ax2.spines[['top','right']].set_visible(False)
    for bar, d in zip(bars, diff):
        ax2.text(bar.get_x()+bar.get_width()/2,
                 bar.get_height() + (8 if d>=0 else -12),
                 f'{d:+.0f}万', ha='center', fontsize=8.5,
                 fontweight='bold', color=(GREEN if d>=0 else RED))
    ax2.set_ylim(min(diff)*1.3, max(abs(v) for v in diff)*0.4)

    # 想定シナリオ注釈
    ax2.axvline(2.5, color=RED, linewidth=1.5, linestyle='--', alpha=0.7)
    ax2.text(2.6, ax2.get_ylim()[0]*0.8, '野村証券\n年末予想\n152.5円', fontsize=7.5,
             color=RED, alpha=0.8)

    # 下部
    rect_b = FancyBboxPatch((0.02,0.02), 0.96, 0.10, boxstyle="round,pad=0.01",
                            lw=0, facecolor='#784212', transform=ax.transAxes)
    ax.add_patch(rect_b)
    points = ["150円到達で約254万円の為替損失（米国資産2784万円ベース）",
              "内需・金融株は円高でもファンダメンタルズ影響が小さい",
              "段階的にシフト。一度に動かさず分散して対応"]
    for i, pt in enumerate(points):
        ax.text(0.04+i*0.33, 0.095, f"! {pt}", fontsize=8.5,
                color=WHITE, fontweight='bold', transform=ax.transAxes)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# スライド 8: 4プラン比較マトリックス
# ════════════════════════════════════════════════════════════════════════════

def slide_comparison():
    fig = new_fig("4プラン 比較マトリックス",
                  "あなたのリスク許容度・投資目標・市場観に応じてプランを選択してください")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # ─ レーダーチャート（各プランの5軸評価）─
    categories = ['リターン\n期待値', 'リスク\n抑制', '円高\n耐性', 'NISA\n活用', '即効性']
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    plan_data = {
        'プランA\n(守り)':  ([3,5,4,2,5], '#1E8B4C'),
        'プランB\n(積立)':  ([4,4,3,5,2], '#2E86C1'),
        'プランC\n(攻め)':  ([5,2,2,4,4], '#8E44AD'),
        'プランD\n(円高)':  ([3,4,5,3,3], '#E67E22'),
    }

    ax_r = fig.add_axes([0.02, 0.10, 0.38, 0.68])
    ax_r.set_facecolor('#F8FBFF')
    ax_r.set_xlim(-1.4,1.4); ax_r.set_ylim(-1.4,1.4); ax_r.axis('off')
    ax_r.set_title('プラン別 評価レーダー', fontsize=12, fontweight='bold', pad=2)

    # グリッド
    for level in [1,2,3,4,5]:
        pts = [[level/5 * np.cos(a), level/5 * np.sin(a)] for a in angles[:-1]]
        pts.append(pts[0])
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ax_r.plot(xs, ys, color=GRAY, linewidth=0.5, alpha=0.4)
    for a in angles[:-1]:
        ax_r.plot([0, np.cos(a)], [0, np.sin(a)], color=GRAY, linewidth=0.5, alpha=0.4)

    for lbl, (scores, clr) in plan_data.items():
        vals = [s/5 for s in scores] + [scores[0]/5]
        xs   = [v * np.cos(a) for v, a in zip(vals, angles)]
        ys   = [v * np.sin(a) for v, a in zip(vals, angles)]
        ax_r.fill(xs, ys, alpha=0.10, color=clr)
        ax_r.plot(xs, ys, color=clr, linewidth=2, label=lbl)

    for cat, angle in zip(categories, angles[:-1]):
        ax_r.text(1.15*np.cos(angle), 1.15*np.sin(angle), cat,
                  ha='center', va='center', fontsize=8.5, fontweight='bold', color=NAVY)
    ax_r.legend(loc='lower center', bbox_to_anchor=(0.5,-0.15), ncol=2, fontsize=9)

    # ─ 比較テーブル ─
    ax_t = fig.add_axes([0.42, 0.10, 0.56, 0.68])
    ax_t.axis('off'); ax_t.set_xlim(0,1); ax_t.set_ylim(0,1)

    headers_t = ["", "プランA\n(守り重視)", "プランB\n(積立継続)", "プランC\n(攻め型)", "プランD\n(円高対応)"]
    rows_t = [
        ("想定期間",        "〜1年",        "5〜10年以上",  "3〜5年",     "1〜2年"),
        ("主な操作",        "一部利確+\n国債追加",
                            "積立増額+\nDRIP",
                            "AI株追加",     "米国株→\n国内株シフト"),
        ("期待リターン",    "★★☆☆☆",     "★★★☆☆",     "★★★★★",  "★★★☆☆"),
        ("リスク水準",      "低",            "中",           "高",          "低〜中"),
        ("円高耐性",        "中〜高",        "中",           "低",          "高"),
        ("NISA活用",        "△",            "◎",            "○",           "○"),
        ("向いている人",    "近く使う\n予定がある",
                            "まだ先の\nゴール",
                            "高リターン\n優先",
                            "円高を\n強く懸念"),
    ]
    col_w = [0.17, 0.20, 0.20, 0.20, 0.20]
    col_x = [0.01]
    for w in col_w[:-1]:
        col_x.append(col_x[-1]+w)
    hdr_colors = [NAVY, '#145A32', BLUE, '#6C3483', '#784212']
    for j, (hdr, cx, cw, hc) in enumerate(zip(headers_t, col_x, col_w, hdr_colors)):
        rect = FancyBboxPatch((cx, 0.92), cw-0.005, 0.065,
                              boxstyle="round,pad=0.002", lw=0, facecolor=hc,
                              transform=ax_t.transAxes)
        ax_t.add_patch(rect)
        ax_t.text(cx+cw/2, 0.953, hdr, ha='center', va='center',
                  fontsize=9, fontweight='bold', color=WHITE,
                  transform=ax_t.transAxes)

    for i, row in enumerate(rows_t):
        bg = '#F5F5F5' if i%2==0 else WHITE
        ry = 0.78 - i*0.117
        for j, (val, cx, cw) in enumerate(zip(row, col_x, col_w)):
            rect = FancyBboxPatch((cx, ry), cw-0.005, 0.108,
                                  boxstyle="round,pad=0.002", lw=0.5,
                                  edgecolor='#CCCCCC', facecolor=bg,
                                  transform=ax_t.transAxes)
            ax_t.add_patch(rect)
            clr = NAVY if j==0 else GRAY
            fw  = 'bold' if j==0 else 'normal'
            ax_t.text(cx+cw/2, ry+0.054, val, ha='center', va='center',
                      fontsize=8.5, color=clr, fontweight=fw,
                      transform=ax_t.transAxes)

    # 下部判断ガイド
    rect_b = FancyBboxPatch((0.02,0.02), 0.96, 0.07, boxstyle="round,pad=0.01",
                            lw=0, facecolor=NAVY, transform=ax.transAxes)
    ax.add_patch(rect_b)
    ax.text(0.5, 0.056, "複数プランの組み合わせも有効。例：「プランB継続 ＋ プランAの一部利確」「プランB基本 ＋ プランCで一部成長株追加」",
            ha='center', fontsize=10, fontweight='bold', color=GOLD,
            transform=ax.transAxes)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# スライド 9: 推奨アクションスケジュール
# ════════════════════════════════════════════════════════════════════════════

def slide_timeline():
    fig = new_fig("推奨アクションスケジュール（今後12ヶ月）",
                  "市場イベントと連動した投資行動のタイムライン")

    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    # タイムライン軸
    ax.axhline(0.55, xmin=0.04, xmax=0.96, color=NAVY, linewidth=2.5)

    months = ['2026/6', '2026/7', '2026/8', '2026/9', '2026/10', '2026/11', '2026/12',
              '2027/1', '2027/2', '2027/3', '2027/4', '2027/5']
    n = len(months)
    xs = [0.05 + i * (0.90/(n-1)) for i in range(n)]

    for i, (x, m) in enumerate(zip(xs, months)):
        ax.plot(x, 0.55, 'o', ms=10, color=BLUE, zorder=5)
        ax.text(x, 0.49, m, ha='center', fontsize=7, color=GRAY, rotation=30)

    # イベント（上部）
    events_up = [
        (0,  "日銀6月\n利上げ決定",    RED,    0.74),
        (2,  "米国\n決算シーズン",      ORANGE, 0.68),
        (5,  "米中間選挙",             PURPLE, 0.74),
        (6,  "日銀12月\n追加利上げ予想", RED,   0.68),
        (11, "米国国債MF164\n満期接近", GREEN,  0.74),
    ]
    for idx, label, clr, y in events_up:
        x = xs[idx]
        ax.annotate('', xy=(x, 0.57), xytext=(x, y-0.06),
                    arrowprops=dict(arrowstyle='->', color=clr, lw=1.5))
        rect = FancyBboxPatch((x-0.055, y-0.06), 0.11, 0.07,
                              boxstyle="round,pad=0.01", lw=1.5,
                              edgecolor=clr, facecolor='white',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x, y-0.025, label, ha='center', va='center',
                fontsize=7.5, color=clr, fontweight='bold',
                transform=ax.transAxes)

    # アクション（下部）
    actions_dn = [
        (0,   GREEN,  0.44, "一部利確\n検討開始"),
        (1,   BLUE,   0.36, "NISA積立\n増額"),
        (3,   ORANGE, 0.44, "高配当株\n追加検討"),
        (4,   PURPLE, 0.36, "AI株\n打診買い"),
        (6,   RED,    0.44, "金融株\n追加（利上げ恩恵）"),
        (8,   ORANGE, 0.36, "円高進行なら\nVTI段階売却"),
        (10,  BLUE,   0.44, "年間NISA枠\n使い切り確認"),
        (11,  GREEN,  0.36, "国債満期\n再投資先検討"),
    ]
    for idx, clr, y, label in actions_dn:
        x = xs[idx]
        ax.annotate('', xy=(x, 0.53), xytext=(x, y+0.07),
                    arrowprops=dict(arrowstyle='->', color=clr, lw=1.5))
        rect = FancyBboxPatch((x-0.055, y-0.01), 0.11, 0.08,
                              boxstyle="round,pad=0.01", lw=1.5,
                              edgecolor=clr, facecolor='#FAFAFA',
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x, y+0.03, label, ha='center', va='center',
                fontsize=7.5, color=clr, fontweight='bold',
                transform=ax.transAxes)

    # 下部注意事項
    rect_b = FancyBboxPatch((0.02,0.01), 0.96, 0.09, boxstyle="round,pad=0.01",
                            lw=1, edgecolor=RED, facecolor='#FFF5F5',
                            transform=ax.transAxes)
    ax.add_patch(rect_b)
    ax.text(0.5, 0.065, "免責事項：本資料は個人ポートフォリオの分析に基づく情報提供です。投資判断は自己責任で行ってください。",
            ha='center', fontsize=9, color=RED, fontweight='bold',
            transform=ax.transAxes)
    ax.text(0.5, 0.030, "市場環境は常に変動します。プランは状況に応じて柔軟に見直してください。",
            ha='center', fontsize=8.5, color=GRAY, transform=ax.transAxes)
    return fig


# ════════════════════════════════════════════════════════════════════════════
# PDF出力
# ════════════════════════════════════════════════════════════════════════════

from PIL import Image

slides = [
    slide_cover,
    slide_market_summary,
    slide_portfolio_analysis,
    slide_plan_a,
    slide_plan_b,
    slide_plan_c,
    slide_plan_d,
    slide_comparison,
    slide_timeline,
]

output_path = "/Users/takahiroazuma/Desktop/kabu/claude/investment_plan.pdf"
A4_W = int(297 * 150 / 25.4)
A4_H = int(210 * 150 / 25.4)

print("投資プランPDFを生成中...")
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

pil_images[0].save(output_path, save_all=True, append_images=pil_images[1:], resolution=150)

size_kb = os.path.getsize(output_path) // 1024
print(f"\n✅ 保存完了: {output_path}")
print(f"   ファイルサイズ: {size_kb} KB / {len(slides)}ページ")
