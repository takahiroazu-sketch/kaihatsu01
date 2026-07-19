# TASKS.md — InvestLog 実装タスク

**対象:** Phase 1（投資日記MVP）  
**目安:** 各タスク 30〜45分  
**作業ルール:** 1タスク完了 → コミット → 次のタスク

---

## Phase 0: プロジェクトセットアップ

- [ ] **T-01** Next.jsプロジェクト作成
  ```bash
  npx create-next-app@latest . --typescript --tailwind --app --import-alias "@/*" --src-dir
  ```
  確認: `npm run dev` でlocalhost:3000が表示される

- [ ] **T-02** 依存パッケージインストール
  ```bash
  npm install @supabase/supabase-js @supabase/ssr
  npm install zod react-hook-form @hookform/resolvers
  npm install recharts sonner
  npm install -D vitest @vitejs/plugin-react @vitest/coverage-v8
  npm install -D @testing-library/react @testing-library/user-event jsdom
  ```

- [ ] **T-03** shadcn/ui 初期化
  ```bash
  npx shadcn@latest init
  npx shadcn@latest add button input label card table dialog textarea select badge
  ```

- [ ] **T-04** tsconfig.json を strict モードに設定
  - `"strict": true` 確認
  - `"noUncheckedIndexedAccess": true` 追加

- [ ] **T-05** vitest.config.ts 作成
  - `src/` 配下のテストを対象
  - jsdom environment設定

- [ ] **T-06** 環境変数ファイル作成
  - `.env.local` (Supabase URL, ANON_KEY, SERVICE_ROLE_KEY)
  - `.env.local.example` (キー名のみ、値なし)
  - `.gitignore` に `.env.local` が含まれることを確認

---

## Phase 1: 型定義・バリデーション

- [ ] **T-07** ドメイン型定義
  - `src/types/trade.ts`
  - `src/types/review.ts`
  - `src/types/api.ts`

- [ ] **T-08** Zodバリデーションスキーマ
  - `src/lib/validations/trade.ts`（CreateTradeSchema, UpdateTradeSchema）
  - `src/lib/validations/review.ts`（CreateReviewSchema, UpdateReviewSchema）

- [ ] **T-09** バリデーションのユニットテスト
  - `src/lib/validations/trade.test.ts`（正常系・異常系 各5ケース以上）
  - `src/lib/validations/review.test.ts`

---

## Phase 2: DB・認証基盤

- [ ] **T-10** Supabaseプロジェクト作成
  - supabase.com でプロジェクト作成
  - URL・ANON_KEY・SERVICE_ROLE_KEY を `.env.local` に設定

- [ ] **T-11** DBマイグレーションSQL作成
  - `supabase/migrations/001_initial.sql`
  - trades テーブル + RLS
  - reviews テーブル + RLS
  - updated_at トリガー

- [ ] **T-12** Supabaseクライアント実装
  - `src/lib/supabase/client.ts`（ブラウザ用シングルトン）
  - `src/lib/supabase/server.ts`（cookie-basedサーバークライアント）

- [ ] **T-13** middleware.ts 実装
  - 保護パス: `/dashboard`, `/trades`, `/analysis`, `/api/`
  - 未認証 → `/login?next=<path>`
  - 認証済 + `/login`,`/register` → `/dashboard`

---

## Phase 3: 認証UI

- [ ] **T-14** ログインページ実装
  - `src/app/(auth)/login/page.tsx`
  - メール + パスワード入力フォーム
  - エラーメッセージ表示
  - 「アカウントを作成」リンク

- [ ] **T-15** 新規登録ページ実装
  - `src/app/(auth)/register/page.tsx`
  - メール + パスワード + 確認パスワード
  - 登録成功 → `/dashboard` リダイレクト

- [ ] **T-16** ログアウト実装
  - `src/components/layout/Header.tsx` にログアウトボタン
  - Server Action で `supabase.auth.signOut()`

---

## Phase 4: 共通レイアウト

- [ ] **T-17** APIハンドラーヘルパー実装
  - `src/lib/api/handler.ts`
  - `apiSuccess<T>(data, status)` / `apiError(message, code, status)`
  - `getAuthUser()` （未認証は401を投げる）

- [ ] **T-18** アプリレイアウト実装
  - `src/app/(app)/layout.tsx`（認証チェック）
  - `src/components/layout/Sidebar.tsx`
  - `src/components/layout/Footer.tsx`（免責表示）

---

## Phase 5: 売買記録API

- [ ] **T-19** GET /api/trades 実装
  - ユーザーの全売買記録を日付降順で返す
  - クエリパラメータ: `limit`, `offset`

- [ ] **T-20** POST /api/trades 実装
  - CreateTradeSchema でバリデーション
  - 201 + { id } を返す

- [ ] **T-21** GET /api/trades/[id] 実装
  - 自分のレコードのみアクセス可（404を返す）
  - reviews テーブルも JOIN して返す

- [ ] **T-22** PATCH /api/trades/[id] 実装
  - UpdateTradeSchema でバリデーション
  - 所有権確認してから更新

- [ ] **T-23** DELETE /api/trades/[id] 実装
  - 所有権確認してから削除
  - 204 No Content

- [ ] **T-24** trades APIのインテグレーションテスト
  - `src/app/api/trades/route.test.ts`
  - Supabaseをモック
  - 201/400/401/422 のレスポンスを検証

---

## Phase 6: 振り返りAPI

- [ ] **T-25** GET /api/reviews/[tradeId] 実装

- [ ] **T-26** POST /api/reviews/[tradeId] 実装
  - tradeId の所有権確認
  - 既に存在する場合は409

- [ ] **T-27** PATCH /api/reviews/[tradeId] 実装

---

## Phase 7: 売買記録UI

- [ ] **T-28** 売買記録一覧ページ実装
  - `src/app/(app)/trades/page.tsx`（Server Component）
  - `src/components/trade/TradeList.tsx`
  - `src/components/trade/TradeCard.tsx`

- [ ] **T-29** 売買記録作成ページ実装
  - `src/app/(app)/trades/new/page.tsx`
  - `src/components/trade/TradeForm.tsx`（react-hook-form + Zod）
  - BUY/SELL切替で表示ラベル変更（「購入理由」/「売却理由」）

- [ ] **T-30** 売買記録詳細・編集ページ実装
  - `src/app/(app)/trades/[id]/page.tsx`
  - 編集モーダル or インライン編集
  - 削除確認ダイアログ

---

## Phase 8: 振り返りUI

- [ ] **T-31** 振り返り入力ページ実装
  - `src/app/(app)/trades/[id]/review/page.tsx`
  - `src/components/review/ReviewForm.tsx`
  - スコア（1〜5）の星評価UI

---

## Phase 9: ダッシュボード

- [ ] **T-32** ダッシュボードページ実装
  - `src/app/(app)/dashboard/page.tsx`（Server Component）
  - `src/components/dashboard/RecentTrades.tsx`（直近10件）
  - 振り返り未記入バッジ表示

---

## Phase 10: テスト・品質

- [ ] **T-33** 全ユニットテスト実行・カバレッジ確認
  ```bash
  npm run test -- --coverage
  ```
  目標: lib/ 配下 80%以上

- [ ] **T-34** TypeScript型チェック
  ```bash
  npm run type-check
  ```
  エラー0件

- [ ] **T-35** 手動E2Eテスト
  - 新規登録 → ログイン → 売買記録作成 → 振り返り入力 → ログアウト
  - スマホサイズ（375px）で全画面確認

---

## Phase 11: 仕上げ・デプロイ

- [ ] **T-36** Vercelプロジェクト作成・デプロイ
  - 環境変数をVercel Dashboardで設定
  - Supabase Redirect URLに本番URLを追加

- [ ] **T-37** README.md 作成
  - セットアップ手順
  - 環境変数一覧
  - デプロイ手順

- [ ] **T-38** 最終確認
  - 本番環境で全機能動作確認
  - フッター免責表示確認
  - RLS動作確認（別ユーザーでデータが見えないか）

---

## 完了チェックリスト

```
□ npm run dev — エラーなし
□ npm run type-check — エラーなし
□ npm run test — 全パス
□ 本番URLでアクセス可能
□ スマホで操作可能
□ 免責表示あり
```
