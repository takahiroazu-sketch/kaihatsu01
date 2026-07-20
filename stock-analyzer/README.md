# stock-analyzer の使い方

このフォルダには、証券コード（日本株4桁）またはティッカー（米国株、例: `VTI`）を指定すると yfinance 経由で株価・財務データを取得し、ファンダメンタルズ／バリュエーション／テクニカルの3分析を行い、ダッシュボード(HTML)やレポート(PDF)を生成する Python ツール一式が入っています。

各スクリプトは「データ取得 → 分析 → 出力」の同じパイプラインを共有しており、どこまでを一括で実行するかで使い分けます。保有銘柄をまとめて解析したいだけなら [`run_holdings.py`](#8-保有銘柄一覧からの一括解析--run_holdingspy) が最短です。個別銘柄を1件だけ試すなら `generate.py`（HTML+PDFを両方作る）で足ります。

| 目的 | 実行するファイル | 出力 |
|---|---|---|
| データ取得のみ（疎通確認） | `fetch_data.py` | `data/<コード>/` にCSV・JSONでキャッシュ |
| 3分析をターミナルに表示 | `analyze.py` | `data/<コード>/analysis.json` |
| 複数銘柄を横並び比較 | `compare.py` | `output/compare_<コード...>.html` |
| ダッシュボード(HTML)のみ | `generate_dashboard.py` | `output/<コード>_dashboard.html` |
| レポート(PDF)のみ | `generate_pdf.py` | `output/<コード>_report.pdf` |
| HTML+PDFを一括生成（銘柄コードを直接指定） | `generate.py` | `output/<コード>_dashboard.html` と `_report.pdf` |
| **保有銘柄一覧から選択銘柄を一括解析（通常はこれを使う）** | `run_holdings.py` | 選択された銘柄ごとに `output/<コード>_dashboard.html` と `_report.pdf` |
| 保有銘柄を横断比較するマトリクスレポート(PDF) | `generate_matrix_report.py` | `output/holdings_matrix_report.pdf` |
| 操作マニュアル(PDF)の再生成 | `generate_manual.py` | `docs/manual.pdf` |

---

## 事前準備

```bash
cd /Users/takahiroazuma/Desktop/kabu/claude/stock-analyzer
pip install pandas numpy yfinance matplotlib pillow
```

すべてのスクリプトは `stock-analyzer` フォルダの中から実行する想定（`data/`・`output/`・`analysis/`・`dashboard/` を相対パス／パッケージとして参照しているため）。

---

## 1. データ取得のみ — `fetch_data.py`

**内容:** 証券コードを1つ渡すと、yfinance から株価（日足1年分）・財務3表（損益計算書／貸借対照表／キャッシュフロー）・主要指標（PER・PBR・配当利回り等）を取得し、取得結果のサマリーをターミナルに表示する。他のすべてのスクリプトが内部でこの `fetch()` 関数を呼び出しており、動作確認用の入り口でもある。

**実行方法:**
```bash
python3 fetch_data.py 7203
```

**出力:** `data/7203/` に `history.csv`（株価）・`income_stmt.csv`・`balance_sheet.csv`・`cashflow.csv`・`dividends.csv`・`info.json` を保存。

---

## 2. 3分析の実行 — `analyze.py`

**内容:** `fetch_data.py` でデータ取得したのち、`analysis/` 配下の3モジュール（下記参照）で分析し、レポート形式でターミナルに表示する。

**実行方法:**
```bash
python3 analyze.py 7203
```

**出力:** `data/7203/analysis.json`（ファンダメンタルズ・バリュエーション・テクニカルの計算結果）。

---

## 3. 複数銘柄比較 — `compare.py`

**内容:** 証券コードを複数渡すと、それぞれ取得・分析したうえで指標を横並びにした比較ダッシュボード(HTML)を1枚生成する。

**実行方法:**
```bash
python3 compare.py 7203 6758 8306
```

**出力:** `output/compare_7203_6758_8306.html`

---

## 4. ダッシュボード(HTML)のみ — `generate_dashboard.py`

**内容:** 証券コードを1つ渡すと、取得・3分析した結果を1銘柄分のHTMLダッシュボードとして出力する。PDFは作らない。

**実行方法:**
```bash
python3 generate_dashboard.py 7203
```

**出力:** `output/7203_dashboard.html`

---

## 5. レポート(PDF)のみ — `generate_pdf.py`

**内容:** 証券コードを1つ渡すと、取得・3分析した結果を承認済みPDFデザインスタイル（[[design_pdf_style]] 参照）でPDFレポートとして出力する。HTMLは作らない。

**実行方法:**
```bash
python3 generate_pdf.py 7203
```

**出力:** `output/7203_report.pdf`

---

## 6. 一括生成（HTML+PDF） — `generate.py`

**内容:** 証券コードを1つ以上渡すと、銘柄ごとにデータ取得・3分析を1回だけ行い、その結果からダッシュボード(HTML)とレポート(PDF)の両方をまとめて生成する。複数コードを渡した場合、1つの銘柄で失敗しても残りは処理を続け、最後に失敗した銘柄コードをまとめて警告表示する。**通常はこのスクリプトを使えばよい。**

**実行方法:**
```bash
python3 generate.py 7203
python3 generate.py 7203 6758 8306
```

**出力:** 渡した銘柄ごとに `output/<コード>_dashboard.html` と `output/<コード>_report.pdf`

---

## 7. 保有銘柄一覧の管理 — `holdings.csv`

**内容:** 保有銘柄をコード管理せずに追加・削除できるようにした一覧ファイル。人が直接編集する前提のCSVで、`run_holdings.py`（次項）が読み込む唯一のデータソース。

| 列名 | 内容 |
|---|---|
| `証券コード` | 日本株の4桁証券コード（例: `7203`）。米国株の場合は空欄でよい。 |
| `ティッカー` | 米国株のティッカー（例: `VTI`, `HDV`）。**この列に値があれば米国株として扱う**。日本株の場合は空欄。 |
| `銘柄名称` | 表示用の銘柄名（分析結果には使われないメモ欄）。 |
| `業種` | 表示用の業種（分析結果には使われないメモ欄）。日本株は東証33業種寄りの分類、米国株はyfinanceの`sector`/`industry`を参考に和訳。ETFは「ETF（〜）」と記載。 |
| `選択` | 解析対象にするかどうか。`1`=選択（対象）、`0`=不選択（対象外）。 |

**編集方法:** テキストエディタでもExcel/Numbersでも直接編集可能。行の追加・削除がそのまま銘柄の追加・削除になる。売却した銘柄は行ごと削除するか、`選択`列を`0`にすれば次回の一括解析から外れる（削除はしたくないが一時的に対象外にしたい場合は後者）。新しい銘柄を追加する際、`業種`が空欄のままだと分析結果には影響しないが一覧の可読性が落ちるので、yfinanceの`info.get("sector")`/`info.get("industry")`等で調べて埋めておくとよい。

**⚠️ 注意点:**
- 日本株・米国株のどちらとして扱うかは `ティッカー` 列の有無だけで判定される（`証券コード`と`ティッカー`を両方埋めた場合は`ティッカー`が優先）。
- `銘柄名称`・`業種`はどちらも解析処理では使われない表示用メモ欄。空欄でも`run_holdings.py`/`generate_matrix_report.py`の動作には影響しない。
- 保有株の増減はSBI証券の「保有証券一覧」エクスポート（`shisan_kanri/data/`）を見ながら手作業で反映する運用。自動同期はしていない。

---

## 8. 保有銘柄一覧からの一括解析 — `run_holdings.py`

**内容:** `holdings.csv` を読み込み、`選択` 列が `1` の行だけを対象に、`generate.py` と同じ処理（データ取得→3分析→ダッシュボード(HTML)+レポート(PDF)生成）をまとめて実行する。日本株（証券コード）・米国株（ティッカー）が混在していても、`holdings.csv` の内容に従って自動判別される。1銘柄が失敗しても残りの処理は続行し、最後に失敗した銘柄をまとめて表示する。

**実行方法:**
```bash
python3 run_holdings.py
python3 run_holdings.py --file holdings.csv   # 別ファイルを使う場合
```

**出力:** 選択された銘柄ごとに `output/<コード>_dashboard.html` と `output/<コード>_report.pdf`

---

## 9. マトリクスレポート(PDF) — `generate_matrix_report.py`

**内容:** `holdings.csv` の選択銘柄（`run_holdings.py`と同じ対象）をすべて取得・分析し、個別銘柄ごとのダッシュボード/レポートとは別に、全銘柄の主要指標（業種・株価・PER・PBR・配当利回り・ROE・直近クロス）を1つの表にまとめて横断比較できるPDFレポートを1本生成する。銘柄数が多い場合は1ページ20行を目安に自動でページを分割する（`ROWS_PER_PAGE`で調整可能）。

**実行方法:**
```bash
python3 generate_matrix_report.py
python3 generate_matrix_report.py --file holdings.csv   # 別ファイルを使う場合
```

**出力:** `output/holdings_matrix_report.pdf`

**⚠️ 注意点:**
- 表の「銘柄」列には `holdings.csv` の `銘柄名称` を、「業種」列には `holdings.csv` の `業種` を優先して使う（`業種`が空欄の場合はyfinanceの`sector`で補完）。yfinanceの英語社名 `longName` は長すぎて列からはみ出すため、`銘柄名称`が空のときのフォールバックとしてのみ使用する。米国株を追加する際は、`銘柄名称`・`業種`をそれぞれ10文字程度に収めておくと表が崩れない。
- `run_holdings.py`（個別レポート）とは別ファイル・別処理として独立している。保有銘柄を追加・削除したら、両方を再実行して整合させること。

---

## 10. 操作マニュアル(PDF)の再生成 — `generate_manual.py`

**内容:** 上記の一括生成・dashboard・report・compare の使い方と出力内容をまとめた操作マニュアルPDF（`docs/manual.pdf`）を、承認済みPDFデザインスタイルで生成する。エンドユーザー向けの操作説明書であり、このREADMEとは目的が異なる（READMEはコードを触る側向け、`docs/manual.pdf` はツールを使う側向け）。

**⚠️ 重要:** ツールに新しい機能を追加したときは、必ずこのスクリプトの該当ページも更新してから再実行し、`docs/manual.pdf` を最新化すること（[[feedback_stock_analyzer_docs_update]] 参照）。

**実行方法:**
```bash
python3 generate_manual.py
```

**出力:** `docs/manual.pdf`

---

## 内部モジュール（直接実行はしない）

上記のスクリプトから呼び出される分析・描画ロジック。単体で実行することはなく、コードを読む・直す際の参照用。

### `analysis/` — 分析ロジック

| ファイル | 役割 |
|---|---|
| `fundamentals.py` | `compute_fundamentals()`。損益計算書・貸借対照表・キャッシュフロー・配当から、期別の売上高・営業益・純利益・ROE・EPS・増収増益フラグなどを計算する。 |
| `valuation.py` | `compute_valuation()`。PER・PBR・PSR・EV/EBITDA・配当利回りに加え、簡易配当割引モデル（ゴードン成長モデル）による理論株価を計算する。 |
| `technical.py` | `compute_technical()`。移動平均線(MA5/25/75/200)・RSI(14)・MACD・ゴールデン/デッドクロス判定・52週高値安値などを計算する。 |

### `dashboard/` — HTML/PDF描画ロジック

| ファイル | 役割 |
|---|---|
| `charts.py` | matplotlibでのチャート描画共通部品（売上高・営業益推移、株価+移動平均線、RSIなど）と配色定数（`BG`, `TEXT`, `TEAL`など）。単一銘柄用。 |
| `compare_charts.py` | `charts.py` を再利用した、複数銘柄比較用の棒グラフ描画。 |
| `render.py` | `render_dashboard()`。単一銘柄のHTMLダッシュボードを組み立てる。 |
| `compare_render.py` | `render_comparison()`。複数銘柄比較用のHTMLを組み立てる（`compare.py` から使用）。 |
| `pdf_report.py` | `build_pdf()`。承認済みPDFデザインスタイル（[[design_pdf_style]]）でmatplotlib図を4ページ分作り、PNG化してPDFに結合する。`generate_manual.py` も内部のページ部品（`new_page`など）を流用している。 |

---

## 共通の注意点

- どのスクリプトも `data/` (fetch_data.pyのキャッシュ) と `output/` (HTML/PDF生成物) を自動で作成する。手動でフォルダを用意する必要はない。
- PDF生成（`generate_pdf.py` / `generate.py` / `generate_manual.py`）は matplotlibの図をPNG化してPillowで1つのPDFに結合する方式（reportlab等は不使用）。図の`axis('off')`を使うと背景色(`facecolor`)が消えることがあるなど、matplotlib特有の罠があるので、新しいページを追加する際は既存ページの書き方（`dashboard/pdf_report.py`）を参考にすること。
- PDFの配色・デザインは承認済みスタイル（オフホワイト背景・黒フッター・ティールアクセント）に統一されている。新しいページ・グラフを追加するときもこのスタイルを踏襲する（[[design_pdf_style]]）。
- 証券コードは日本株の4桁コード（例: `7203`）と米国株のティッカー（例: `VTI`）の両方に対応。`fetch_data.to_yahoo_ticker()` が数字のみのコードには `.T` を付与し、英字を含むティッカーはそのまま使う。そのため `fetch_data.py`・`analyze.py`・`compare.py`・`generate*.py` はどれも引数にティッカーを直接渡せる（例: `python3 generate.py 7203 VTI`）。
- 米国ETF等、yfinanceから損益計算書（income statement）が取得できない銘柄はファンダメンタルズ分析のタイムラインが空になる。`page_fundamentals`（`dashboard/pdf_report.py`）はこの場合「損益計算書データはありません」というプレースホルダーページを出す（空リストのままテーブル描画すると`ax.table()`が`list index out of range`で落ちるため）。
