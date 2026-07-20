# shisan_kanri の使い方

このフォルダには、SBI証券の保有データをもとにPDF/PowerPointレポートを作る Python スクリプトが入っています。
同じ内容のスクリプトが `_v2`, `_v3`, `_v4` のように複数バージョンあるものは、**番号が一番大きいものだけが現役**です。古いバージョン（無印や `_v1`〜`_v3`）は過去の試作なので、通常は触らなくて大丈夫です。

現役スクリプトは以下の6本です。

| 目的 | 現役ファイル | 出力 |
|---|---|---|
| 配当金の分析レポート | `create_dividend_pdf_v4.py` | `output/dividend_report_v4.pdf` |
| 保有証券ポートフォリオの分析レポート | `create_portfolio_pdf_v2.py` | `output/portfolio_report_v2.pdf` |
| 投資プラン提案書 | `create_investment_plan_v4.py` | `output/investment_plan_v4.pdf` |
| 配当金の推移グラフ＋利回りマトリクス | `create_dividend_analysis_v1.py` | `output/dividend_analysis_v1.pdf` |
| 個別株パフォーマンス分析 | `create_performance_report_v1.py` | `output/stock_performance_v1.pdf` |
| ポートフォリオ（PowerPoint版） | `create_portfolio_pptx.py` | `portfolio_report.pptx` |

---

## 1. 配当金の分析レポート — `create_dividend_pdf_v4.py`

**内容:** 表紙／年別推移／月別パターン／日本株銘柄別／米国株・ETF・米国債銘柄別／全銘柄ランキング（全6ページ）

**使うデータ:**
- `data/DISTRIBUTION_YYYYMMDDHHMMSS.csv`（SBI証券からエクスポートした配当金履歴）
- スクリプト内の `CSV_HIST` 変数で1本のファイル名を指定している。最新ファイルはそれ以前の全期間を含む累積データなので、**最新の1ファイルだけを指定すればよい**。

**データを更新するとき:**
1. SBI証券から配当金履歴を新しくエクスポートし、`data/` に置く
2. スクリプト冒頭の `CSV_HIST = f"{DATA_DIR}/DISTRIBUTION_XXXXXXXXXXXXXX.csv"` を新しいファイル名に書き換える
3. 本文中の日付表示（表紙・フッター・年別ラベルなど、`7月11日`のように書かれている箇所）も新しい基準日に合わせて手直しする

**実行方法:**
```bash
cd /Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri
python3 create_dividend_pdf_v4.py
```

---

## 2. 保有証券ポートフォリオの分析レポート — `create_portfolio_pdf_v2.py`

**内容:** 表紙／全体概要／日本株ランキング／セクター分析／NISA口座／投資信託／米国株／米国債／運用成績まとめ／特徴と注目銘柄（全10ページ）

**使うデータ:** CSVを直接読み込む方式ではなく、**保有銘柄のデータ（評価額・評価損益など）はスクリプト冒頭に直接書き込まれている**（`jp_tokutei`, `jp_nisa_growth`, `us_tokutei` などのリスト）。SBI証券の「保有証券一覧」画面のエクスポートを見ながら、これらの数値を手作業で書き換える必要がある。

エクスポート形式は2種類ある:
- 旧形式（`data/*SaveFile.csv` + `data/YYMMDDus.csv` の2ファイル）: 米国株・米国債の円換算額が入っておらず、USD/JPY実勢レートを別途確認してJPY換算する必要があった。
- 新形式（`data/YYYYMMDD_jp_us.csv` の1ファイルに日本株・投信・米国株・米国債すべてを含む、2026/7/19以降で確認）: 米国株・米国債にも「円換算評価損益」「円換算評価額」の列がそのまま入っているので、**為替レートを別途確認する必要がなくなった**。今後もこの形式でエクスポートできるなら、こちらを優先して使う。

**⚠️ 重要な注意点:**
- 同じ数値（セクター別合計・NISA銘柄テーブル・「注目銘柄」ハイライトの騰落率など）が**スクリプト内の複数箇所に分散してハードコードされている**。データを更新するときは、変更前の古い数値が他の場所に残っていないか `grep` で確認してから実行するのが安全。
- 保有銘柄が売却されて0件になった場合（例: 2026/7に旧NISAのSKYTを全株売却）、該当リスト（例: `us_old_nisa`）を空リストにするだけでなく、そのリストを前提にした件数表示（「旧NISA1」等）・凡例・ハイライト文言も合わせて洗い出して修正すること。
- 保有株の売却で現金残高（`sbi_usd_cash` / `sbi_jpy_cash`）が変わる場合、CSVには預り金情報が入っていないので、実際の売却代金の入金先・金額をユーザーに確認してから反映すること。
- 出力先が過去に `shisan_kanri/output/` の外を指すバグがあったため（2026/7/11に修正済み）、スクリプトの `OUT` 変数が `shisan_kanri/output/` 配下を指しているか一応確認すること。

**実行方法:**
```bash
cd /Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri
python3 create_portfolio_pdf_v2.py
```

---

## 3. 投資プラン提案書 — `create_investment_plan_v4.py`

**内容:** 表紙／資産合計サマリー／楽天証券口座／SWOT分析／現金比率／プランA〜D／プラン比較／実行タイムライン（全11ページ）

**使うデータ:** `create_portfolio_pdf_v2.py` と同様、保有データはスクリプト冒頭に直接ハードコードされている。ポートフォリオレポートを更新したときは、こちらの数値も合わせて見直す必要がある。

**⚠️ 注意点:**
- 楽天証券のデータ（`rakuten_vti_*`, `rakuten_spcx_*` 等）と現金（`CASH`）はSBIの保有データとは別に管理されており、SBI側のデータを更新してもここは自動更新されない。楽天側の残高が変わった場合は別途手動更新が必要。
- SWOT分析・プランA〜D内の文章にも、資産額や騰落率がその都度ハードコードされている（例:「VTI系への集中リスク...約1,792万円」「米国資産の為替リスク...約2,539万円」）。保有データを更新した際はこれらの文章も整合するよう手動で書き換えること。
- 保有銘柄が売却済みになった場合（例: SKYT）は、プランの提案アクション（SELL等）が既に実行済みであることが分かるよう文言を書き換える（`DONE`ステータス等）。

**実行方法:**
```bash
cd /Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri
python3 create_investment_plan_v4.py
```

---

## 4. 配当金の推移グラフ＋利回りマトリクス — `create_dividend_analysis_v1.py`

（バージョン違いが無く、これが唯一かつ現役のファイル）

**内容:** 銘柄別の配当推移スモールマルチプル／ヒートマップ／利回りランキング（全3ページ）

**使うデータ:**
- `data/DISTRIBUTION_...csv`（配当金履歴、2ファイルを結合して読む古い方式のまま）
- `data/260619jp.csv`（日本株保有明細）

**⚠️ 注意点:** `create_dividend_pdf_v4.py` とは違い、配当金CSVを2ファイル結合方式のまま読んでいる、かつ日本株保有明細のファイル名が固定（`260619jp.csv`）でやや古いデータを参照している。データを更新する場合は、このスクリプト内の `CSV_HIST` / `CSV_2026` / `PORT_CSV` を新しいファイル名に書き換える必要がある。

**実行方法:**
```bash
cd /Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri
python3 create_dividend_analysis_v1.py
```

---

## 5. 個別株パフォーマンス分析 — `create_performance_report_v1.py`

（バージョン違いが無く、これが唯一かつ現役のファイル）

**内容:** 表紙／資産推移／配当金履歴／配当成長／サマリー／注目銘柄（全6ページ）

**使うデータ:**
- 米国株の評価額・損益はスクリプト内に直接ハードコード（`US` 辞書）
- `DIV_CSV = 'data/DISTRIBUTION_20260627095220.csv'`（配当金履歴、**相対パス**指定）

**⚠️ 注意点:** データ・出力パスの両方が相対パス（`data/...`, `output/...`）で書かれているため、**必ず `shisan_kanri` フォルダの中から実行する**こと。別の場所から実行するとファイルが見つからずエラーになる。

**実行方法:**
```bash
cd /Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri
python3 create_performance_report_v1.py
```

---

## 6. ポートフォリオ（PowerPoint版） — `create_portfolio_pptx.py`

（バージョン違いが無く、これが唯一かつ現役のファイル）

**内容:** `create_portfolio_pdf.py`（PDF版）と同じ内容をPowerPoint形式で出力するもの。保有データはスクリプト内に直接ハードコード。

**⚠️ 注意点:**
- 出力先が `/Users/takahiroazuma/Desktop/kabu/claude/portfolio_report.pptx`（`shisan_kanri` フォルダの外）を指している。既存ファイルは `shisan_kanri/output/portfolio_report.pptx` にあるため、実行後は出力場所を確認し、必要なら手動で移動すること。
- `python-pptx` ライブラリが必要（`pip install python-pptx`）。

**実行方法:**
```bash
cd /Users/takahiroazuma/Desktop/kabu/claude/shisan_kanri
python3 create_portfolio_pptx.py
```

---

## 共通の注意点

- どのスクリプトも matplotlib・Pillow（PIL）を使うので、初回は `pip install matplotlib pandas numpy pillow` が必要（PowerPoint版のみ追加で `python-pptx` も必要）。
- 出力PDF/PPTXは基本的に `output/` フォルダに作られる想定だが、スクリプトによっては `shisan_kanri` フォルダの外を指しているものがある（上記の注意点を参照）。実行後は必ず生成物の場所を確認すること。
- 保有データがハードコードされているスクリプト（ポートフォリオ系・投資プラン・パフォーマンス分析・PowerPoint版）は、SBI証券のエクスポートCSVを見ながら**手作業で数値を書き換える**運用になっている。データを自動でCSVから読み込む仕組みではないので、更新時は書き換え漏れに注意する。
