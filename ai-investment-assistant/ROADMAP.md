# 開発ロードマップ — KabuAI（2週間 MVP）

**開始日:** 2026-06-29（月）  
**完成目標:** 2026-07-12（日）

---

## 全体スケジュール

```
Week 1: 基盤 + コア機能
Week 2: AI機能 + UI仕上げ + デプロイ

     Mon  Tue  Wed  Thu  Fri  Sat  Sun
W1:  D1   D2   D3   D4   D5   D6   D7
W2:  D8   D9   D10  D11  D12  D13  D14
```

---

## Week 1: 基盤 + コア機能

### Day 1（月）— プロジェクトセットアップ

**目標:** `npm run dev` で画面が表示される状態

- [ ] Next.js 15 プロジェクト作成（TypeScript, Tailwind, App Router）
  ```bash
  npx create-next-app@latest kabuai --typescript --tailwind --app
  ```
- [ ] shadcn/ui 初期化
  ```bash
  npx shadcn@latest init
  npx shadcn@latest add button input card table dialog
  ```
- [ ] Supabase プロジェクト作成（supabase.com）
- [ ] Supabase 環境変数を `.env.local` に設定
- [ ] Supabase クライアント設定（`lib/supabase/client.ts`, `server.ts`）
- [ ] Git リポジトリ初期化 + GitHub リモート作成

**成果物:** localhost:3000 でトップページ表示

---

### Day 2（火）— 認証実装

**目標:** ログイン・登録・ログアウトが動く

- [ ] Supabase Auth 設定（メール認証有効化）
- [ ] ログインページ (`/login`) 実装
- [ ] 新規登録ページ (`/register`) 実装
- [ ] パスワードリセットページ実装
- [ ] `middleware.ts` で認証ガード実装
- [ ] 認証後のリダイレクト処理
- [ ] Google OAuth 設定（オプション）

**テスト:** メール登録→ログイン→ダッシュボードへリダイレクト確認

---

### Day 3（水）— DB + ポートフォリオ CRUD

**目標:** ポートフォリオの追加・表示ができる

- [ ] Supabase で DB テーブル作成（`DB_DESIGN.md` の SQL 実行）
  - `portfolios` テーブル
  - `holdings` テーブル
  - RLS ポリシー設定
- [ ] `/api/portfolios` Route Handler 実装（GET / POST）
- [ ] `/api/holdings` Route Handler 実装（POST）
- [ ] ポートフォリオ一覧ページ (`/portfolio`) 実装
- [ ] 保有銘柄追加モーダル (`AddHoldingModal`) 実装
- [ ] Zod バリデーション実装

**テスト:** ポートフォリオ作成 → 銘柄追加 → 一覧表示確認

---

### Day 4（木）— 株価データ連携

**目標:** 保有銘柄に現在株価が表示される

- [ ] 株価取得ロジック実装 (`lib/prices/fetcher.ts`)
  - 日本株: Yahoo Finance JP（`*.T` 形式）
  - 米国株: Yahoo Finance US
- [ ] 為替レート取得 (ExchangeRate-API)
- [ ] `/api/prices` Route Handler 実装
- [ ] Next.js キャッシュ設定（revalidate: 900）
- [ ] `HoldingCard` に損益計算を組み込み
- [ ] ローディング状態（Skeleton UI）実装

**テスト:** 7203・AAPL の株価取得・損益計算確認

---

### Day 5（金）— ダッシュボード

**目標:** 損益サマリーダッシュボードが完成

- [ ] ダッシュボードページ (`/dashboard`) 実装
- [ ] `PnLSummary` コンポーネント（総評価額・評価損益）
- [ ] `HoldingTable` コンポーネント（銘柄別一覧・ソート）
- [ ] `AllocationChart` コンポーネント（Recharts 円グラフ）
- [ ] サイドバーナビゲーション実装

**テスト:** ダッシュボードで全銘柄の損益確認

---

### Day 6（土）— バッファ / 品質改善

**目標:** Week 1 の積み残し解消 + UI 調整

- [ ] Day 1〜5 の積み残しタスク消化
- [ ] 銘柄編集・削除機能の実装
- [ ] エラーハンドリング改善
- [ ] モバイルレスポンシブ確認・調整
- [ ] `PATCH /api/holdings/[id]`、`DELETE /api/holdings/[id]` 実装

---

### Day 7（日）— Week 1 レビュー

- [ ] 全機能の動作確認（E2E テスト手動）
- [ ] Supabase RLS が正しく動いているか確認
- [ ] コードリファクタリング
- [ ] Week 2 タスクの優先度調整

---

## Week 2: AI機能 + 仕上げ + デプロイ

### Day 8（月）— AI チャット基盤

**目標:** Claude API とのチャットが動く

- [ ] `@anthropic-ai/sdk` インストール
- [ ] `lib/ai/claude.ts` — Claude API ラッパー実装
- [ ] `lib/ai/prompts.ts` — システムプロンプト構築関数
  - ポートフォリオ情報の自動埋め込み
  - 根拠のない推奨を禁じるガードレール
  - 免責文の自動付加
- [ ] `chat_sessions` / `chat_messages` テーブル作成 + RLS
- [ ] `/api/chat` Route Handler — ストリーミング実装

**テスト:** curl で `/api/chat` にリクエスト → ストリーミング応答確認

---

### Day 9（火）— チャット UI 実装

**目標:** チャット画面でAIと会話できる

- [ ] チャットページ (`/chat`) 実装
- [ ] `ChatWindow` コンポーネント（SSE 受信・逐次表示）
- [ ] `MessageBubble` コンポーネント（user / assistant 表示）
- [ ] クイック質問ボタン実装
- [ ] チャット履歴のロード実装
- [ ] タイピングアニメーション（`...`）

**テスト:** 「トヨタは売るべきか？」と質問 → 根拠ある回答を確認

---

### Day 10（水）— プロンプト改善 + ガードレール

**目標:** AI 応答の品質・安全性を高める

- [ ] システムプロンプトの精度向上（反復テスト）
- [ ] ガードレール強化
  - 根拠のない推奨を確実にブロック
  - 危険な集中投資への警告
- [ ] 「この銘柄の分析をして」ボタン（S-06 からチャット遷移）
- [ ] チャット履歴ページ（セッション一覧）
- [ ] AI エラー時のフォールバック UI

---

### Day 11（木）— Vercel デプロイ

**目標:** 本番環境で動作する

- [ ] Vercel プロジェクト作成・連携
- [ ] 環境変数設定（Vercel Dashboard）
- [ ] `next.config.ts` の最終確認
- [ ] 本番ドメインで Supabase の Redirect URL 更新
- [ ] 本番環境での全機能動作確認
- [ ] Google OAuth の Redirect URI 更新

---

### Day 12（金）— UI 仕上げ

**目標:** 見た目・使い勝手の最終調整

- [ ] フッターに免責表示追加（法的必須）
- [ ] ファビコン・OGP 画像設定
- [ ] ローディング状態の統一
- [ ] 空状態（保有銘柄ゼロ時）のエンプティステート UI
- [ ] フォームの UX 改善（オートフォーカス等）
- [ ] SP でのチャット画面最適化

---

### Day 13（土）— テスト + バグ修正

**目標:** 人に見せられる品質

- [ ] ユーザー登録から全機能のフローを 3 回通しテスト
- [ ] 株価取得エラー時の挙動確認
- [ ] Claude API レート制限時の挙動確認
- [ ] 発見バグの修正
- [ ] パフォーマンス確認（LCP < 2秒）

---

### Day 14（日）— リリース

**目標:** MVP 完成・身内公開

- [ ] 最終動作確認
- [ ] README.md 作成（セットアップ手順）
- [ ] 身内・知人に URL 共有
- [ ] フィードバック収集開始
- [ ] v2 機能の backlog 整理

---

## リスクと対策

| リスク | 発生確率 | 対策 |
|--------|---------|------|
| J-Quants API の取得が複雑 | 高 | Day 4 で Yahoo Finance JP に切替え（スクレイピング or 非公式） |
| 株価 API のレート制限 | 中 | Next.js キャッシュ 15分 + バッチ取得で回数削減 |
| Claude API コスト増大 | 低 | max_tokens=1024 に制限、1日の利用回数制限を検討 |
| 認証バグによるデータ漏洩 | 低 | RLS で二重防御、Day 7 で集中確認 |
| デプロイ環境変数の設定ミス | 中 | Day 11 にチェックリスト用意 |

---

## 作業時間見積もり

```
1日あたりの作業可能時間: 3〜4時間（個人開発・平日夜 + 休日）

Day 1〜5（平日）: 約 3.5h × 5 = 17.5h
Day 6〜7（週末）: 約 5h × 2 = 10h
Day 8〜12（平日）: 約 3.5h × 5 = 17.5h
Day 13〜14（週末）: 約 5h × 2 = 10h

合計: 約 55時間
```

---

## 完了定義（MVP Done）

```
✅ メール認証でログイン・ログアウトができる
✅ ポートフォリオに銘柄を追加・編集・削除できる
✅ ダッシュボードで現在の損益が確認できる（日本株・米国株・為替対応）
✅ AI チャットでポートフォリオについて質問できる
✅ AI は根拠のない銘柄推奨をしない
✅ 免責表示が適切に表示されている
✅ Vercel で本番デプロイされており、URLでアクセスできる
✅ スマホで操作できる（レスポンシブ）
```
