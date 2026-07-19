"""複数銘柄比較用チャート。既存の charts.py の配色・スタイルを再利用する。"""

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from dashboard.charts import BG, TEXT, TEXT2, TEAL, AMBER, chart_style, fig_to_data_uri

BAR_COLORS = [TEAL, AMBER, "#8870CC", "#2D8A50", "#C03030", "#5BAED0"]


def draw_metric_bar(ax, names, values, title, fmt="{:.1f}"):
    """値の大きい順に横棒グラフを描く。値がNoneの銘柄は「データなし」として0扱いで最下段に表示。"""
    pairs = [(n, v) for n, v in zip(names, values)]
    pairs.sort(key=lambda p: (p[1] is None, -(p[1] or 0)))
    names_sorted = [p[0] for p in pairs][::-1]
    values_sorted = [p[1] for p in pairs][::-1]
    plot_values = [v if v is not None else 0 for v in values_sorted]

    chart_style(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color="#C8C4BE", lw=0.6)

    colors = [BAR_COLORS[i % len(BAR_COLORS)] for i in range(len(names_sorted))]
    bars = ax.barh(range(len(names_sorted)), plot_values, color=colors, height=0.6)
    ax.set_yticks(range(len(names_sorted)))
    ax.set_yticklabels(names_sorted, fontsize=9.5)

    max_v = max(plot_values) if plot_values else 1
    min_v = min(plot_values) if plot_values else 0
    span = max(max_v, 0) - min(min_v, 0)
    pad = span * 0.15 if span > 0 else 1

    if min_v < 0:
        ax.axvline(0, color=TEXT2, lw=0.8)

    for bar, v in zip(bars, values_sorted):
        label = fmt.format(v) if v is not None else "―"
        offset = pad * 0.15
        x = bar.get_width() + offset if bar.get_width() >= 0 else bar.get_width() - offset
        ha = "left" if bar.get_width() >= 0 else "right"
        ax.text(x, bar.get_y() + bar.get_height() / 2,
                label, va="center", ha=ha, fontsize=9, fontweight="bold", color=TEXT)

    ax.set_xlim(min(min_v, 0) - pad, max(max_v, 0) + pad)
    ax.set_title(title, fontsize=12, color=TEXT, loc="left", pad=10)


def metric_bar_chart(names, values, title, fmt="{:.1f}") -> str:
    fig = plt.figure(figsize=(6.0, 0.6 * len(names) + 1.0), facecolor=BG)
    draw_metric_bar(fig.add_subplot(111), names, values, title, fmt)
    return fig_to_data_uri(fig)
