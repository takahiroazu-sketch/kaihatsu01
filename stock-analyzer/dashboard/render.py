"""分析結果(JSON互換のdict)からダッシュボードHTMLを組み立てる。"""

from datetime import datetime
from html import escape

import pandas as pd

from dashboard.charts import revenue_profit_chart, price_ma_chart, rsi_chart

CSS = """
:root {
  --bg: #EDEAE6;
  --bg-card: #F5F2EE;
  --bg-card-alt: #E4E0DA;
  --text: #1A1A1A;
  --text-muted: #6B6560;
  --teal: #00B4CC;
  --amber: #D4820C;
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
    --bg-card-alt: #26272B;
    --text: #ECE8E2;
    --text-muted: #9B948C;
    --teal: #22C7DE;
    --amber: #E6944A;
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
.wrap { max-width: 960px; margin: 0 auto; padding: 0 24px; }
.hero { padding: 48px 0 32px; border-bottom: 1px solid var(--border); }
.hero .code { font-family: ui-monospace, "SF Mono", Menlo, monospace; color: var(--text-muted); font-size: 13px; letter-spacing: 0.06em; }
.hero h1 { font-size: 30px; margin: 6px 0 4px; }
.hero .sub { color: var(--text-muted); font-size: 14px; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 24px; }
.kpi { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }
.kpi .label { font-size: 11.5px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.kpi .value { font-family: ui-monospace, monospace; font-size: 20px; font-weight: 600; margin-top: 4px; }
.flag { display: inline-block; margin-top: 20px; padding: 6px 14px; border-radius: 100px; font-size: 13px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-muted); }
.flag b { color: var(--text); }
.section { padding: 40px 0; border-bottom: 1px solid var(--border); }
.section h2 { font-size: 20px; margin: 0 0 18px; }
.chart-card { background: #EDEAE6; border-radius: 10px; padding: 12px; border: 1px solid var(--border); }
.chart-card img { display: block; width: 100%; height: auto; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.table-scroll { overflow-x: auto; margin-top: 18px; }
table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
th, td { text-align: right; padding: 10px 12px; border-bottom: 1px solid var(--border); font-variant-numeric: tabular-nums; }
th:first-child, td:first-child { text-align: left; }
th { color: var(--text-muted); font-weight: 600; font-size: 11.5px; letter-spacing: 0.03em; text-transform: uppercase; background: var(--hdrbg); }
.pos { color: var(--pos); }
.neg { color: var(--neg); }
.note { border-left: 3px solid var(--teal); background: var(--bg-card); padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 13px; color: var(--text-muted); margin-top: 16px; }
.footer { background: var(--footer-bg); color: var(--footer-text); padding: 22px 0; }
.footer .wrap { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-size: 12px; }
.footer .disclaimer { opacity: 0.75; max-width: 60ch; }
@media (max-width: 700px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .grid-2 { grid-template-columns: 1fr; }
}
"""


def _has_value(v):
    return isinstance(v, (int, float)) and not pd.isna(v)


def _yen(v):
    return f"{v:,.0f}円" if _has_value(v) else "―"


def _oku(v):
    return f"{v / 1e8:,.0f}億円" if _has_value(v) else "―"


def _pct(v, digits=1):
    return f"{v * 100:.{digits}f}%" if _has_value(v) else "―"


def _ratio(v):
    return f"{v:.1f}倍" if _has_value(v) else "―"


def _num(v, digits=1):
    return f"{v:,.{digits}f}" if _has_value(v) else "―"


def _signed_class(v):
    if not _has_value(v):
        return ""
    return "pos" if v >= 0 else "neg"


def _fundamentals_table(timeline: list) -> str:
    rows = []
    for t in timeline:
        rows.append(f"""
        <tr>
          <td>{escape(t['period'])}</td>
          <td>{_oku(t['revenue'])}</td>
          <td class="{_signed_class(t['operating_income'])}">{_oku(t['operating_income'])}</td>
          <td class="{_signed_class(t['net_income'])}">{_oku(t['net_income'])}</td>
          <td>{_pct(t['operating_margin'])}</td>
          <td>{_pct(t['net_margin'])}</td>
          <td class="{_signed_class(t['roe'])}">{_pct(t['roe'])}</td>
          <td>{_num(t['eps'])}円</td>
          <td>{_num(t['dividend_per_share'])}円</td>
        </tr>""")
    return f"""
    <div class="table-scroll">
      <table>
        <thead><tr>
          <th>期</th><th>売上高</th><th>営業利益</th><th>純利益</th>
          <th>営業利益率</th><th>純利益率</th><th>ROE</th><th>EPS</th><th>配当/株</th>
        </tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>"""


def _valuation_table(v: dict) -> str:
    rows = [
        ("株価", _yen(v["latest_close"])),
        ("PER（実績）", _ratio(v["trailing_per"])),
        ("PER（予想）", _ratio(v["forward_per"])),
        ("PBR", _ratio(v["pbr"])),
        ("PSR", _ratio(v["psr"])),
        ("EV/EBITDA", _ratio(v["ev_to_ebitda"])),
        ("配当利回り", _pct(v["dividend_yield"])),
        ("理論株価（簡易DDM）", _yen(v["theoretical_price_ddm"])),
    ]
    trs = "".join(f"<tr><td>{k}</td><td>{val}</td></tr>" for k, val in rows)
    assumptions = v.get("ddm_assumptions") or {}
    note = ""
    if assumptions:
        note = f"""<div class="note">簡易DDM前提: 要求利回り {_pct(assumptions.get('required_return'))} /
        想定配当成長率 {_pct(assumptions.get('dividend_growth_rate'))}。
        理論株価は簡易モデルによる参考値であり、投資判断はご自身の責任で行ってください。</div>"""
    return f"""
    <div class="table-scroll">
      <table><tbody>{trs}</tbody></table>
    </div>{note}"""


def _technical_summary(t: dict) -> str:
    cross = t["cross_signal"]
    ma = t["moving_averages"]
    macd = t["macd"]
    sr = t["support_resistance"]
    vol = t["volume"]
    rows = [
        ("MA5 / MA25 / MA75 / MA200", f"{_yen(ma['ma5'])} / {_yen(ma['ma25'])} / {_yen(ma['ma75'])} / {_yen(ma['ma200'])}"),
        ("RSI(14)", _num(t["rsi_14"])),
        ("MACD / シグナル / ヒストグラム", f"{_num(macd['macd'])} / {_num(macd['signal'])} / {_num(macd['histogram'])}"),
        (f"直近クロス（{cross['ma_pair']}）", f"{cross['type'] or '―'}（{cross['date'] or '―'}）"),
        ("52週高値 / 安値", f"{_yen(sr['range_52w_high'])} / {_yen(sr['range_52w_low'])}"),
        ("直近20日 高値 / 安値", f"{_yen(sr['range_20d_high'])} / {_yen(sr['range_20d_low'])}"),
        ("出来高（直近 / 20日平均）", f"{vol['latest']:,} / {vol['avg_20d']:,.0f}"),
    ]
    trs = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows)
    return f'<div class="table-scroll"><table><tbody>{trs}</tbody></table></div>'


def render_dashboard(code: str, info: dict, history, fundamentals: dict, valuation: dict, technical: dict) -> str:
    latest = fundamentals["latest"]
    flags = fundamentals["trend_flags"]

    company_name = info.get("longName") or code
    sector = info.get("sector") or "―"
    industry = info.get("industry") or "―"

    revenue_chart_uri = revenue_profit_chart(fundamentals["timeline"])
    price_chart_uri = price_ma_chart(history)
    rsi_chart_uri = rsi_chart(history)

    if flags["zoushu_zoueki"]:
        zoushu_zoueki = "増収増益"
    else:
        revenue_label = "増収" if flags["revenue_yoy_growth"] else "減収"
        profit_label = "増益" if flags["net_income_yoy_growth"] else "減益"
        zoushu_zoueki = f"{revenue_label}・{profit_label}"

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{escape(company_name)}（{escape(code)}）銘柄分析ダッシュボード</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{CSS}</style>
</head>
<body>
<div class="hero">
  <div class="wrap">
    <div class="code">{escape(code)} ・ {escape(sector)} / {escape(industry)}</div>
    <h1>{escape(company_name)}</h1>
    <div class="sub">終値 {_yen(technical['latest_close'])}（{technical['latest_date']}時点）</div>
    <div class="kpis">
      <div class="kpi"><div class="label">PER（実績）</div><div class="value">{_ratio(valuation['trailing_per'])}</div></div>
      <div class="kpi"><div class="label">PBR</div><div class="value">{_ratio(valuation['pbr'])}</div></div>
      <div class="kpi"><div class="label">配当利回り</div><div class="value">{_pct(valuation['dividend_yield'])}</div></div>
      <div class="kpi"><div class="label">ROE（最新期）</div><div class="value">{_pct(latest.get('roe'))}</div></div>
    </div>
    <div class="flag"><b>{zoushu_zoueki}</b>（直近期 vs 前期）</div>
  </div>
</div>

<div class="section">
  <div class="wrap">
    <h2>1. ファンダメンタルズ分析</h2>
    <div class="chart-card"><img src="{revenue_chart_uri}" alt="売上高・純利益の推移"></div>
    {_fundamentals_table(fundamentals["timeline"])}
  </div>
</div>

<div class="section">
  <div class="wrap">
    <h2>2. バリュエーション分析</h2>
    {_valuation_table(valuation)}
  </div>
</div>

<div class="section">
  <div class="wrap">
    <h2>3. テクニカル分析</h2>
    <div class="grid-2">
      <div class="chart-card"><img src="{price_chart_uri}" alt="株価と移動平均線"></div>
      <div class="chart-card"><img src="{rsi_chart_uri}" alt="RSI"></div>
    </div>
    {_technical_summary(technical)}
  </div>
</div>

<div class="footer">
  <div class="wrap">
    <div class="disclaimer">本レポートはユーザーが指定した銘柄コードの分析結果を提示するものであり、ツール側から独自の銘柄推奨は行いません。投資判断はご自身の責任で行ってください。</div>
    <div>生成日時: {generated_at}</div>
  </div>
</div>
</body>
</html>"""
