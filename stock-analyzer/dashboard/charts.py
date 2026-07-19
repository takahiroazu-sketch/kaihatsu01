"""チャート生成（HTMLダッシュボード・PDFレポート共通）。

配色・グラフスタイルは承認済みPDFレポートスタイル（オフホワイト背景・ティールアクセント）を踏襲する。
`draw_*` 系は既存の Axes に描画するだけの関数で、HTML用の単体画像化(`*_chart`)とPDFのページ
レイアウトの両方から呼び出せる。
"""

import base64
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter

_JP_FONT = next((f.name for f in fm.fontManager.ttflist
                  if f.name in ["Hiragino Sans", "Hiragino Kaku Gothic ProN",
                                 "Yu Gothic", "Noto Sans CJK JP"]), None)
if _JP_FONT:
    plt.rcParams["font.family"] = _JP_FONT
plt.rcParams["axes.unicode_minus"] = False

BG = "#EDEAE6"
TEXT = "#1A1A1A"
TEXT2 = "#6B6560"
TEAL = "#00B4CC"
AMBER = "#D4820C"
GRID = "#C8C4BE"
SPINE = "#C0BCB8"


def chart_style(ax):
    ax.set_facecolor(BG)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.xaxis.grid(False)
    ax.spines["bottom"].set_color(SPINE)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="both", length=0, labelsize=9.5, colors=TEXT2)


def fig_to_data_uri(fig) -> str:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def draw_revenue_profit(ax, timeline: list):
    periods = [t["period"] for t in timeline]
    revenue = [(t["revenue"] or 0) / 1e8 for t in timeline]
    net_income = [(t["net_income"] or 0) / 1e8 for t in timeline]

    chart_style(ax)
    x = range(len(periods))
    width = 0.36
    ax.bar([i - width / 2 for i in x], revenue, width=width, color=TEAL, label="売上高")
    ax.bar([i + width / 2 for i in x], net_income, width=width, color=AMBER, label="純利益")

    ax.set_xticks(list(x))
    ax.set_xticklabels(periods)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}億円"))
    ax.legend(frameon=False, fontsize=9.5, labelcolor=TEXT2, loc="upper left")
    ax.set_title("売上高・純利益の推移", fontsize=12, color=TEXT, loc="left", pad=10)


def draw_price_ma(ax, history, ma_windows=(25, 75), lookback=180):
    hist = history.tail(lookback)
    close = hist["Close"]

    chart_style(ax)
    ax.plot(hist.index, close, color=TEXT, lw=1.4, label="終値")
    colors = [TEAL, AMBER]
    for window, color in zip(ma_windows, colors):
        ma = history["Close"].rolling(window).mean().tail(lookback)
        ax.plot(hist.index, ma, color=color, lw=1.1, label=f"MA{window}")

    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}円"))
    ax.legend(frameon=False, fontsize=9.5, labelcolor=TEXT2, loc="upper left")
    ax.set_title("株価と移動平均線", fontsize=12, color=TEXT, loc="left", pad=10)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")


def draw_rsi(ax, history, lookback=180):
    close = history["Close"]
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14).mean()
    rsi = 100 - (100 / (1 + avg_gain / avg_loss))
    rsi_tail = rsi.tail(lookback)

    chart_style(ax)
    ax.plot(rsi_tail.index, rsi_tail, color=TEAL, lw=1.3)
    ax.axhline(70, color=TEXT2, lw=0.8, ls="--")
    ax.axhline(30, color=TEXT2, lw=0.8, ls="--")
    ax.set_ylim(0, 100)
    ax.set_title("RSI (14日)", fontsize=12, color=TEXT, loc="left", pad=10)
    ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=6))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")


def revenue_profit_chart(timeline: list) -> str:
    fig = plt.figure(figsize=(6.4, 3.4), facecolor=BG)
    draw_revenue_profit(fig.add_subplot(111), timeline)
    return fig_to_data_uri(fig)


def price_ma_chart(history, ma_windows=(25, 75), lookback=180) -> str:
    fig = plt.figure(figsize=(6.4, 3.0), facecolor=BG)
    draw_price_ma(fig.add_subplot(111), history, ma_windows, lookback)
    return fig_to_data_uri(fig)


def rsi_chart(history, lookback=180) -> str:
    fig = plt.figure(figsize=(6.4, 2.0), facecolor=BG)
    draw_rsi(fig.add_subplot(111), history, lookback)
    return fig_to_data_uri(fig)
