"""複数銘柄比較ダッシュボードのHTML組み立て。"""

from datetime import datetime
from html import escape

import pandas as pd

from dashboard.compare_charts import metric_bar_chart

CSS = """
:root {
  --bg: #EDEAE6;
  --bg-card: #F5F2EE;
  --text: #1A1A1A;
  --text-muted: #6B6560;
  --teal: #00B4CC;
  --pos: #2D8A50;
  --neg: #C03030;
  --border: #D0CCC8;
  --footer-bg: #1C1C1C;
  --footer-text: #EDEAE6;
  --hdrbg: #D4D0CC;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #17181A;
    --bg-card: #202124;
    --text: #ECE8E2;
    --text-muted: #9B948C;
    --teal: #22C7DE;
    --pos: #4CAF6E;
    --neg: #E0605F;
    --border: #35363A;
    --footer-bg: #0E0E0F;
    --footer-text: #ECE8E2;
    --hdrbg: #2C2D30;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Hiragino Sans", "Yu Gothic", "Meiryo", -apple-system, sans-serif;
  line-height: 1.7;
}
.wrap { max-width: 1040px; margin: 0 auto; padding: 0 24px; }
.hero { padding: 48px 0 28px; border-bottom: 1px solid var(--border); }
.hero .eyebrow { font-size: 12.5px; letter-spacing: 0.08em; color: var(--text-muted); text-transform: uppercase; }
.hero h1 { font-size: 26px; margin: 8px 0 4px; }
.hero .sub { color: var(--text-muted); font-size: 14px; }
.section { padding: 36px 0; border-bottom: 1px solid var(--border); }
.section h2 { font-size: 19px; margin: 0 0 16px; }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
th, td { text-align: right; padding: 10px 12px; border-bottom: 1px solid var(--border); font-variant-numeric: tabular-nums; }
th:first-child, td:first-child { text-align: left; }
th { color: var(--text-muted); font-weight: 600; font-size: 11.5px; letter-spacing: 0.03em; text-transform: uppercase; background: var(--hdrbg); }
.pos { color: var(--pos); }
.neg { color: var(--neg); }
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.chart-card { background: #EDEAE6; border-radius: 10px; padding: 12px; border: 1px solid var(--border); }
.chart-card img { display: block; width: 100%; height: auto; }
.footer { background: var(--footer-bg); color: var(--footer-text); padding: 22px 0; }
.footer .wrap { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-size: 12px; }
.footer .disclaimer { opacity: 0.75; max-width: 60ch; }
@media (max-width: 700px) {
  .chart-grid { grid-template-columns: 1fr; }
}
"""


def _yen(v):
    return f"{v:,.0f}円" if isinstance(v, (int, float)) and not pd.isna(v) else "―"


def _pct(v):
    return f"{v * 100:.1f}%" if isinstance(v, (int, float)) and not pd.isna(v) else "―"


def _ratio(v):
    return f"{v:.1f}倍" if isinstance(v, (int, float)) and not pd.isna(v) else "―"


def _signed_class(v):
    if not isinstance(v, (int, float)) or pd.isna(v):
        return ""
    return "pos" if v >= 0 else "neg"


def render_comparison(entries: list) -> str:
    """entries: [{"code":..., "info":..., "fundamentals":..., "valuation":..., "technical":...}, ...]"""
    names = [e["info"].get("longName") or e["code"] for e in entries]
    codes = [e["code"] for e in entries]

    rows = []
    for e in entries:
        latest = e["fundamentals"]["latest"]
        v = e["valuation"]
        t = e["technical"]
        rows.append(f"""
        <tr>
          <td>{escape(e['info'].get('longName') or e['code'])}（{escape(e['code'])}）</td>
          <td>{_yen(t['latest_close'])}</td>
          <td>{_ratio(v['trailing_per'])}</td>
          <td>{_ratio(v['pbr'])}</td>
          <td>{_pct(v['dividend_yield'])}</td>
          <td class="{_signed_class(latest.get('roe'))}">{_pct(latest.get('roe'))}</td>
          <td>{t['cross_signal']['type'] or '―'}</td>
        </tr>""")

    def _to_pct(v):
        return v * 100 if isinstance(v, (int, float)) and not pd.isna(v) else None

    per_chart = metric_bar_chart(names, [e["valuation"]["trailing_per"] for e in entries],
                                  "PER（実績）比較", fmt="{:.1f}倍")
    roe_chart = metric_bar_chart(names, [_to_pct(e["fundamentals"]["latest"].get("roe")) for e in entries],
                                  "ROE 比較（%）", fmt="{:.1f}%")
    yield_chart = metric_bar_chart(names, [_to_pct(e["valuation"]["dividend_yield"]) for e in entries],
                                    "配当利回り 比較（%）", fmt="{:.1f}%")
    pbr_chart = metric_bar_chart(names, [e["valuation"]["pbr"] for e in entries],
                                  "PBR 比較", fmt="{:.1f}倍")

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    codes_label = " / ".join(codes)

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>複数銘柄比較ダッシュボード（{escape(codes_label)}）</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{CSS}</style>
</head>
<body>
<div class="hero">
  <div class="wrap">
    <div class="eyebrow">複数銘柄比較</div>
    <h1>{escape(codes_label)}</h1>
    <div class="sub">{len(entries)}銘柄を比較（{generated_at} 時点）</div>
  </div>
</div>

<div class="section">
  <div class="wrap">
    <h2>指標一覧</h2>
    <div class="table-scroll">
      <table>
        <thead><tr>
          <th>銘柄</th><th>株価</th><th>PER（実績）</th><th>PBR</th><th>配当利回り</th><th>ROE（最新期）</th><th>直近クロス</th>
        </tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </div>
</div>

<div class="section">
  <div class="wrap">
    <h2>指標比較チャート</h2>
    <div class="chart-grid">
      <div class="chart-card"><img src="{per_chart}" alt="PER比較"></div>
      <div class="chart-card"><img src="{pbr_chart}" alt="PBR比較"></div>
      <div class="chart-card"><img src="{roe_chart}" alt="ROE比較"></div>
      <div class="chart-card"><img src="{yield_chart}" alt="配当利回り比較"></div>
    </div>
  </div>
</div>

<div class="footer">
  <div class="wrap">
    <div class="disclaimer">本レポートはユーザーが指定した銘柄コードの分析結果を比較表示するものであり、ツール側から独自の銘柄推奨は行いません。投資判断はご自身の責任で行ってください。</div>
    <div>生成日時: {generated_at}</div>
  </div>
</div>
</body>
</html>"""
