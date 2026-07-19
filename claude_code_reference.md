# Claude Code 機能一覧リファレンス

作成日: 2026-07-05
目的: Claude Code（このAIコーディングツール）が使えるコマンド・スキル・ツール・サブエージェントを整理し、後から見直せるようにする。

---

## 1. 組み込みスラッシュコマンド（CLI標準機能）

スキルではなく、Claude Code本体に組み込まれている基本コマンド。

| コマンド | 説明 |
|---|---|
| `/help` | Claude Codeの使い方に関するヘルプを表示 |
| `/clear` | 会話履歴をクリアする |
| `/config` | テーマ・モデルなど基本設定を変更する |
| `/fast` | Fast modeの切り替え（Opusで高速出力。モデルを下げるわけではない） |
| `/remember` | ユーザーの好み・情報をメモリに保存する |

---

## 2. スキル（スラッシュコマンドとして呼び出し可能）

`/スキル名` の形式で呼び出す。ユーザーが明示的に入力するか、タスク内容が合致したときにClaudeが自動判断して使用する。

| スキル名 | 呼び出し例 | 説明 |
|---|---|---|
| `dataviz` | 自動発動 | グラフ・チャート・ダッシュボード等のデータ可視化を作る前に必ず読み込む設計ガイド。配色・レイアウトのルールを規定 |
| `artifact-design` | 自動発動 | Artifact（HTML/Markdownの共有ページ）作成時のデザイン方針ガイド |
| `update-config` | `/update-config` | `settings.json`の設定変更（権限追加、フック設定、環境変数など） |
| `keybindings-help` | `/keybindings-help` | キーボードショートカットのカスタマイズ・リバインド |
| `verify` | `/verify` | コード変更が実際に意図通り動くかを実際に動かして検証する |
| `code-review` | `/code-review [low\|medium\|high\|xhigh\|max\|ultra]` | 現在の差分をバグ・簡略化の観点でレビュー。`ultra`はクラウド上でのマルチエージェントレビュー（課金あり） |
| `simplify` | `/simplify` | 変更箇所のコードを再利用性・簡潔性・効率の観点で見直し、修正まで適用 |
| `fewer-permission-prompts` | `/fewer-permission-prompts` | 過去の操作履歴から許可プロンプトを減らすための許可リストを生成 |
| `loop` | `/loop [間隔] コマンド` | 特定のプロンプト/コマンドを一定間隔、または自己ペースで繰り返し実行 |
| `schedule` | `/schedule` | cronベースのクラウドエージェント（定期実行タスク）の作成・管理 |
| `claude-api` | 自動発動 | Claude API/Anthropic SDKに関する質問（料金・モデルID・制限等）が出た際に必ず参照するリファレンス |
| `run` | `/run` | プロジェクトのアプリを実際に起動して動作確認・スクリーンショット取得 |
| `init` | `/init` | 新規`CLAUDE.md`（コードベース説明ファイル）の初期化 |
| `review` | `/review` | GitHubのプルリクエストをレビュー（ローカル差分は`code-review`を使用） |
| `security-review` | `/security-review` | 現在のブランチの変更内容についてセキュリティレビューを実施 |

---

## 3. 主要ツール（内部動作用）

Claudeが裏側で使うツール群。ユーザーが直接呼ぶものではないが、権限確認プロンプトの元になる。

| ツール名 | 説明 |
|---|---|
| `Bash` | シェルコマンドを実行（git操作、ビルド、テスト実行など） |
| `Read` | ファイル内容を読み込む（画像・PDF・Jupyter Notebookにも対応） |
| `Edit` | 既存ファイルの一部を文字列置換で編集 |
| `Write` | ファイルを新規作成・全体書き換え |
| `Agent` | サブエージェントを立ち上げて複雑なタスクを委任（下記4参照） |
| `Artifact` | HTML/MarkdownをWebページ化してユーザーに共有（デフォルト非公開） |
| `AskUserQuestion` | ユーザー自身にしか判断できない選択について質問する |
| `Skill` | 上記スキルを呼び出す |
| `ToolSearch` | 使用頻度の低い「遅延ツール」のスキーマを検索・読み込む |
| `ReportFindings` | コードレビュー結果を構造化して報告 |
| `ScheduleWakeup` | `/loop`の自己ペースモードで次回実行タイミングを予約 |
| `TodoWrite`※ | タスクリストを作成・進捗管理（※遅延ツール） |

### 遅延ツール（ToolSearchで都度読み込み）

| ツール名 | 説明 |
|---|---|
| `WebFetch` | 指定URLの内容を取得 |
| `WebSearch` | Web検索を実行 |
| `NotebookEdit` | Jupyter Notebookのセル編集 |
| `EnterPlanMode` / `ExitPlanMode` | 計画モードの開始・終了（実装前にユーザー承認を得る） |
| `EnterWorktree` / `ExitWorktree` | git worktree（作業ツリー）の切り替え |
| `Monitor` | バックグラウンドプロセスのイベントをストリーム監視 |
| `TaskOutput` / `TaskStop` | バックグラウンドタスクの出力取得・停止 |
| `SendMessage` | 実行中のサブエージェントにメッセージを送って再開させる |
| `CronCreate` / `CronList` / `CronDelete` | 定期実行cronジョブの作成・一覧・削除 |
| `PushNotification` | プッシュ通知の送信 |
| `RemoteTrigger` | リモート実行のトリガー |
| `DesignSync` | デザイン同期関連 |

---

## 4. サブエージェントの種類（Agentツールで指定）

| エージェント名 | 用途 |
|---|---|
| `claude` | 特定のエージェントに当てはまらない汎用タスクのデフォルト |
| `claude-code-guide` | Claude Code本体・Agent SDK・Claude APIに関する質問対応 |
| `Explore` | 読み取り専用の高速コード検索（ファイル特定、シンボル検索など） |
| `general-purpose` | 複雑な調査・複数ステップのタスクを丸ごと委任 |
| `Plan` | 実装計画の設計（アーキテクチャ設計・トレードオフ検討） |
| `statusline-setup` | ステータスライン設定のセットアップ |

---

## 補足メモ

- `/ultrareview` は `/code-review ultra` の非推奨エイリアス（同じ機能）
- スキルの多くはスラッシュコマンドと1:1対応するが、`dataviz`・`artifact-design`・`claude-api` は自動発動型（該当タスク時にClaudeが自律的に読み込む）
- 本ファイルは2026-07-05時点のClaude Code機能構成に基づく。ツール構成はアップデートで変わる可能性があるため、内容が古くなっていないか適宜確認すること
