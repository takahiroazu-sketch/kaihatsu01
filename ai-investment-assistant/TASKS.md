# 実装タスクリスト — KabuAI

**目安:** 各タスク ≈ 30分  
**合計:** 63タスク  
**参照:** `TECH_DESIGN.md` にコード例あり

---

## 凡例

```
[ ] 未着手   [x] 完了   [~] 進行中   [!] ブロック中
```

各タスクの末尾 `→ ✓` は「完了の確認方法」

---

## Phase 1: プロジェクトセットアップ（Day 1）

- [ ] **[T-01] Next.js プロジェクト作成**
  `npx create-next-app@latest kabuai --typescript --tailwind --app --import-alias "@/*"` を実行し、不要なサンプルファイル（`app/page.tsx` の中身）を空にする  
  → ✓ `npm run dev` で localhost:3000 が表示される

- [ ] **[T-02] 依存パッケージ一括インストール**
  `@supabase/ssr`, `@supabase/supabase-js`, `@anthropic-ai/sdk`, `swr`, `zustand`, `zod`, `@hookform/resolvers`, `react-hook-form`, `recharts`, `sonner` をインストール  
  → ✓ `npm ls` でエラーなし

- [ ] **[T-03] shadcn/ui セットアップ**
  `npx shadcn@latest init` → `button`, `input`, `card`, `table`, `dialog`, `select`, `form`, `label`, `alert`, `badge`, `separator`, `skeleton` を追加  
  → ✓ `components/ui/` ディレクトリにファイル群が生成されている

- [ ] **[T-04] 環境変数・Git 初期設定**
  `.env.local`（Supabase URL/KEY, ANTHROPIC_API_KEY）と `.env.example`（値なし）を作成。`.gitignore` に `.env.local` を追加。GitHub リポジトリ作成 + 初回 push  
  → ✓ GitHub 上にリポジトリが見える、`.env.local` が push されていない

---

## Phase 2: 型定義（Day 2 前半）

- [ ] **[T-05] `types/` 全ファイル作成**
  `types/portfolio.ts`, `types/holding.ts`, `types/chat.ts`, `types/api.ts` を `TECH_DESIGN.md § 2-1` のコードで作成  
  → ✓ `npx tsc --noEmit` がエラーなし

- [ ] **[T-06] Zod バリデーションスキーマ作成**
  `lib/validations/holding.ts`（`CreateHoldingSchema`, `UpdateHoldingSchema`）と `lib/validations/portfolio.ts`（`CreatePortfolioSchema`）を `TECH_DESIGN.md § 7-7` のコードで作成  
  → ✓ `tsc --noEmit` がエラーなし

- [ ] **[T-07] ユーティリティ関数作成**
  `lib/utils/currency.ts`（`formatCurrency`, `formatRate`）と `lib/utils/pnl.ts`（`enrichHoldingsWithPnL`, `calcPortfolioSummary`）を `TECH_DESIGN.md § 2-7` のコードで作成  
  → ✓ `tsc --noEmit` がエラーなし

---

## Phase 3: DB・マイグレーション（Day 2 後半）

- [ ] **[T-08] Supabase プロジェクト作成 + CLI 設定**
  supabase.com でプロジェクト作成、`npx supabase init`, `npx supabase login`。URL/ANON_KEY/SERVICE_ROLE_KEY を `.env.local` に記入  
  → ✓ `npx supabase status` が接続成功

- [ ] **[T-09] マイグレーション SQL 作成 + 実行**
  `supabase/migrations/001_initial.sql` を `TECH_DESIGN.md § 4-1` の SQL で作成し、Supabase Dashboard の SQL Editor で実行  
  → ✓ Dashboard の Table Editor に `portfolios`, `holdings`, `chat_sessions`, `chat_messages` が表示される

- [ ] **[T-10] TypeScript 型自動生成**
  `npx supabase gen types typescript --project-id <project-id> > lib/supabase/database.types.ts` を実行。`TECH_DESIGN.md § 4-2` の手書き型と突き合わせ確認  
  → ✓ `database.types.ts` に 4テーブル分の Row/Insert/Update 型がある

---

## Phase 4: 認証実装（Day 3）

- [ ] **[T-11] Supabase クライアント 3種作成**
  `lib/supabase/client.ts`（ブラウザ用シングルトン）、`lib/supabase/server.ts`（Cookie 対応 Server Component 用）、`lib/supabase/admin.ts`（service_role 用）を `TECH_DESIGN.md § 5-2` のコードで作成  
  → ✓ `tsc --noEmit` がエラーなし

- [ ] **[T-12] `middleware.ts` 実装**
  `TECH_DESIGN.md § 5-3` のコードで `middleware.ts` を作成。保護ルート・認証ルートを定義し、未認証時に `/login?next=<元のパス>` へリダイレクト  
  → ✓ ブラウザで `/dashboard` にアクセスすると `/login` にリダイレクトされる

- [ ] **[T-13] `(auth)/layout.tsx` + ログインページ実装**
  `app/(auth)/layout.tsx`（中央揃えラッパー）と `app/(auth)/login/page.tsx` を `TECH_DESIGN.md § 5-4` のコードで実装。メールログインフォーム + Google OAuth ボタンを含む  
  → ✓ フォーム送信後にエラーメッセージが出る（認証前だから）

- [ ] **[T-14] 新規登録ページ + Auth Callback 実装**
  `app/(auth)/register/page.tsx`（メール/パスワード/確認入力）と `app/auth/callback/route.ts`（OAuth コールバック処理）を実装  
  → ✓ テストユーザーでメール登録 → 確認メール受信 → ログイン成功

- [ ] **[T-15] ログアウト処理 + `(app)/layout.tsx` 骨格作成**
  Sidebar にログアウトボタンを仮置き。`app/(app)/layout.tsx` をサイドバー付き2カラムレイアウトで作成（Sidebar は空でも可）  
  → ✓ ログイン後 `/dashboard` に遷移し、2カラムレイアウトが見える

---

## Phase 5: API 共通基盤（Day 4 前半）

- [ ] **[T-16] API ハンドラー共通ラッパー作成**
  `lib/api/handler.ts`（`apiError`, `apiSuccess`, `getAuthUser`）を `TECH_DESIGN.md § 3-1` のコードで作成  
  → ✓ `tsc --noEmit` がエラーなし

- [ ] **[T-17] エラークラス + `apiFetch` ラッパー作成**
  `lib/errors.ts`（`AppError`, `PriceFetchError`, `PortfolioNotFoundError`）と `lib/fetcher.ts`（401時の自動リダイレクト付きfetch ラッパー）を `TECH_DESIGN.md § 6-2,6-5` のコードで作成  
  → ✓ `tsc --noEmit` がエラーなし

- [ ] **[T-18] トースト通知 + ErrorBoundary セットアップ**
  `app/layout.tsx` に `<Toaster />` を追加（sonner）。`lib/toast.ts`（`notify.success/error/loading`）と `components/shared/ErrorBoundary.tsx` を `TECH_DESIGN.md § 6-3,6-4` のコードで作成  
  → ✓ ブラウザコンソールで `notify.success('テスト')` を呼ぶとトーストが出る

---

## Phase 6: ポートフォリオ API（Day 4 後半〜Day 5 前半）

- [ ] **[T-19] `GET/POST /api/portfolios` 実装**
  `app/api/portfolios/route.ts` を `TECH_DESIGN.md § 3-2` のコードで実装。認証チェック + Supabase CRUD + Zod バリデーション  
  → ✓ `curl -X POST /api/portfolios` で 401 が返る（未認証）

- [ ] **[T-20] `GET/PATCH/DELETE /api/portfolios/[id]` 実装**
  `app/api/portfolios/[id]/route.ts` を実装。所有者確認（`user_id = auth.uid()`）を必ず行う  
  → ✓ 他ユーザーの portfolio_id で DELETE すると 403 が返る

- [ ] **[T-21] `GET /api/portfolios/[id]/holdings` 実装**
  `app/api/portfolios/[id]/holdings/route.ts` で保有銘柄一覧を返す。RLS で自動フィルタリング  
  → ✓ 認証済みで GET するとホールディング一覧の JSON が返る

- [ ] **[T-22] `POST /api/holdings` 実装**
  `app/api/holdings/route.ts` を `TECH_DESIGN.md § 3-3` のコードで実装。ポートフォリオ所有者確認 + 重複銘柄チェック（`23505` エラーハンドリング）  
  → ✓ 同じ銘柄を2回 POST すると 422 が返る

- [ ] **[T-23] `PATCH/DELETE /api/holdings/[id]` 実装**
  `app/api/holdings/[id]/route.ts` を実装。PATCH は `UpdateHoldingSchema`（partial）でバリデーション。DELETE は所有者確認後に削除  
  → ✓ DELETE 後に GET すると 404 が返る

---

## Phase 7: 株価取得（Day 5 後半〜Day 6 前半）

- [ ] **[T-24] 日本株価取得関数**
  `lib/prices/japan.ts` を `TECH_DESIGN.md § 3-4` のコードで実装。Yahoo Finance JP API から `{code}.T` 形式で取得。失敗時は空オブジェクトを返す（個別失敗を無視）  
  → ✓ 関数単体で `7203` の株価オブジェクトが取れる

- [ ] **[T-25] 米国株価取得関数 + 為替取得関数**
  `lib/prices/us.ts`（Yahoo Finance US）と `lib/prices/forex.ts`（ExchangeRate-API）を実装。エラー時は `{ USDJPY: 150 }` をフォールバックとして返す  
  → ✓ 関数単体で `AAPL` の株価と `USDJPY` の為替が取れる

- [ ] **[T-26] 株価統合 fetcher + API Route 実装**
  `lib/prices/fetcher.ts`（`Promise.allSettled` で日米株・為替を並行取得）と `app/api/prices/route.ts`（15分 Cache-Control 付き）を `TECH_DESIGN.md § 3-4` のコードで実装  
  → ✓ `GET /api/prices?codes=7203,AAPL` で prices + forex の JSON が返る

- [ ] **[T-27] `usePrices` カスタムフック**
  `hooks/usePrices.ts` を `TECH_DESIGN.md § 2-6` のコードで実装。SWR + 15分ごとの自動再取得  
  → ✓ コンポーネントに組み込んで株価が表示される

---

## Phase 8: レイアウト・共通 UI（Day 6 後半）

- [ ] **[T-28] Sidebar コンポーネント**
  `components/layout/Sidebar.tsx` を実装。ナビゲーションリンク（ダッシュボード/ポートフォリオ/チャット）、`usePathname()` で現在ページをハイライト、ログアウトボタン  
  → ✓ 各リンクをクリックすると対応ページに遷移する

- [ ] **[T-29] `DisclaimerFooter` + `EmptyState` + `LoadingSkeleton`**
  `components/layout/DisclaimerFooter.tsx`（免責文）、`components/shared/EmptyState.tsx`（アイコン+メッセージ+CTAボタン）、`components/shared/LoadingSkeleton.tsx`（Skeleton UI ラッパー）を実装  
  → ✓ `/portfolio` に銘柄が0件のとき EmptyState が表示される

- [ ] **[T-30] `uiStore.ts` (Zustand) 作成**
  `stores/uiStore.ts` で「AddHoldingModal の開閉状態」を管理する Zustand ストアを作成  
  → ✓ `useUiStore(s => s.isAddModalOpen)` でモーダル状態が取れる

---

## Phase 9: ポートフォリオ UI（Day 7 前半）

- [ ] **[T-31] `usePortfolio` カスタムフック**
  `hooks/usePortfolio.ts` を SWR ベースで実装。`addHolding`, `updateHolding`, `deleteHolding` のミューテーション関数も含む（楽観的更新は不要）  
  → ✓ フックから `addHolding()` を呼ぶと DB に登録される

- [ ] **[T-32] `AddHoldingModal` コンポーネント**
  `components/portfolio/AddHoldingModal.tsx` を `TECH_DESIGN.md § 2-4` のコードで実装。react-hook-form + zod でバリデーション、成功後にモーダルを閉じてリストを再取得  
  → ✓ フォームに不正値（保有数=0）を入力するとバリデーションエラーが表示される

- [ ] **[T-33] `HoldingCard` コンポーネント**
  `components/portfolio/HoldingCard.tsx` を実装。銘柄名・コード・保有数・取得単価・現在値・損益を表示。編集ボタン（モーダル展開）・削除ボタン（確認ダイアログ）を含む  
  → ✓ 削除ボタンを押すと確認後に DB から消える

- [ ] **[T-34] ポートフォリオページ (`/portfolio`)**
  `app/(app)/portfolio/page.tsx`（Server Component：初期データ取得）と `app/(app)/portfolio/loading.tsx`（Skeleton）を実装。HoldingCard リスト + AddHoldingModal を組み合わせる  
  → ✓ `/portfolio` で銘柄一覧が表示される

---

## Phase 10: ダッシュボード UI（Day 7 後半〜Day 8）

- [ ] **[T-35] `PnLSummary` コンポーネント**
  `components/dashboard/PnLSummary.tsx` を `TECH_DESIGN.md § 2-3` のコードで実装。総評価額・評価損益・損益率の 3カードを表示。プラス/マイナスで文字色を切り替える  
  → ✓ 損益がプラスで緑、マイナスで赤になる

- [ ] **[T-36] `AllocationChart` コンポーネント**
  `components/dashboard/AllocationChart.tsx` を Recharts `PieChart` で実装。銘柄を市場（JP/US）別に集計、評価額ベースで比率を表示  
  → ✓ 日本株と米国株の比率が円グラフで見える

- [ ] **[T-37] `HoldingTable` コンポーネント**
  `components/dashboard/HoldingTable.tsx` を実装。損益率でソート可能なテーブル（銘柄名 / 保有数 / 現在値 / 評価額 / 損益 / 損益率）  
  → ✓ 損益率カラムをクリックするとソートされる

- [ ] **[T-38] ダッシュボードページ (`/dashboard`)**
  `app/(app)/dashboard/page.tsx`（Server Component）を実装。Supabase からポートフォリオ+銘柄を取得し、`usePrices` + `enrichHoldingsWithPnL` で損益計算してコンポーネントに渡す  
  → ✓ ログイン後 `/dashboard` に総評価額が表示される

---

## Phase 11: AI チャット Backend（Day 9）

- [ ] **[T-39] `lib/ai/prompts.ts` 実装**
  `buildSystemPrompt(portfolio, holdingsWithPnL, forex)` を `TECH_DESIGN.md § 3-6` のコードで実装。ガードレール指示（根拠のない推奨禁止・免責文必須）をシステムプロンプトに組み込む  
  → ✓ 関数を呼ぶと日本語の詳細なシステムプロンプト文字列が返る

- [ ] **[T-40] `lib/ai/claude.ts` 実装**
  Anthropic SDK のシングルトンインスタンスを `lib/ai/claude.ts` で export。`model: 'claude-sonnet-4-6'`, `max_tokens: 1024` をデフォルト設定として定義  
  → ✓ `tsc --noEmit` がエラーなし

- [ ] **[T-41] `chat_sessions` / `chat_messages` テーブルの RLS 確認**
  Supabase Dashboard で `chat_sessions` と `chat_messages` の RLS ポリシーが有効か確認。`TECH_DESIGN.md § 4-1` の SQL を再確認して適用漏れを修正  
  → ✓ `auth.uid()` と異なる user_id での SELECT が空配列になる

- [ ] **[T-42] `POST /api/chat` 実装（ストリーミング）**
  `app/api/chat/route.ts` を `TECH_DESIGN.md § 3-5` のコードで実装。ポートフォリオ取得 → 株価取得 → プロンプト構築 → Claude API ストリーミング → SSE 転送 → DB 保存  
  → ✓ `curl -N -X POST /api/chat -d '{"portfolioId":"...","message":"こんにちは"}'` でストリーミングレスポンスが返る

---

## Phase 12: AI チャット Frontend（Day 10）

- [ ] **[T-43] `useChat` カスタムフック**
  `hooks/useChat.ts` を `TECH_DESIGN.md § 2-6` のコードで実装。SSE 受信・逐次メッセージ追加・セッション ID 管理・エラー時フォールバックメッセージを含む  
  → ✓ `sendMessage('テスト')` を呼ぶと messages が1件増える

- [ ] **[T-44] `MessageBubble` + `ChatInput` コンポーネント**
  `components/chat/MessageBubble.tsx`（role に応じて左右配置・ストリーミング時のアニメーション）と `components/chat/ChatInput.tsx`（Enter送信・Shift+Enterで改行・送信中は無効化）を実装  
  → ✓ Enter を押すと送信、Shift+Enter で改行できる

- [ ] **[T-45] `QuickQuestions` コンポーネント**
  `components/chat/QuickQuestions.tsx` を実装。メッセージ0件時に表示する定型文ボタン4種（「ポートフォリオ全体の評価」「含み損銘柄の対処法」「分散状況を確認」「今月の相場動向」）  
  → ✓ ボタンをクリックすると ChatInput に文字列がセットされて送信される

- [ ] **[T-46] `ChatWindow` コンポーネント**
  `components/chat/ChatWindow.tsx` を `TECH_DESIGN.md § 2-5` のコードで実装。スクロール末尾への自動追従（`useEffect` + `scrollIntoView`）と DisclaimerBanner を含む  
  → ✓ メッセージが増えると自動で下にスクロールする

- [ ] **[T-47] チャットページ (`/chat`)**
  `app/(app)/chat/page.tsx`（'use client'）を実装。デフォルトポートフォリオの ID を取得して `ChatWindow` に渡す。`app/(app)/chat/loading.tsx`（Skeleton）も作成  
  → ✓ AI に「こんにちは」と入力するとストリーミング応答が表示される

---

## Phase 13: ポリッシュ（Day 11〜12）

- [ ] **[T-48] loading.tsx を全ページに追加**
  `dashboard/loading.tsx`, `portfolio/loading.tsx`, `chat/loading.tsx` に Skeleton UI を実装。カードのシマーアニメーションを shadcn の `<Skeleton>` で表現  
  → ✓ ページ遷移中にシマーアニメーションが表示される

- [ ] **[T-49] モバイルレスポンシブ対応（サイドバー）**
  SP ではサイドバーをハンバーガーメニュー（シート）に変更。`Sheet` コンポーネント（shadcn）を使い、md 以上では常時表示、md 未満ではオーバーレイにする  
  → ✓ iPhone サイズでサイドバーがハンバーガーメニューになる

- [ ] **[T-50] モバイルレスポンシブ対応（チャット）**
  SP でのチャット画面を最適化。キーボード表示時に入力欄が隠れないよう `h-dvh` を使った高さ制御  
  → ✓ スマホでキーボードを開いても入力欄が見える

- [ ] **[T-51] 空状態・エラー状態の UI 統一**
  保有銘柄ゼロ時・チャット初回時・株価取得失敗時の EmptyState / エラーメッセージを全ページで確認し、統一する  
  → ✓ 各エラー状態で適切なメッセージが出る

- [ ] **[T-52] ファビコン・メタ情報設定**
  `app/layout.tsx` の `metadata` にサイト名・説明・OGP 画像（仮）を設定。`app/favicon.ico` を配置  
  → ✓ ブラウザタブにサイト名が表示される

---

## Phase 14: テスト（Day 13）

- [ ] **[T-53] Vitest 設定 + テスト環境構築**
  `vitest.config.ts` を `TECH_DESIGN.md § 7-5` のコードで作成。`package.json` に `test`, `test:watch`, `test:coverage` スクリプトを追加  
  → ✓ `npm run test` が実行できる（テストファイルなしでも 0 passed で完了）

- [ ] **[T-54] 損益計算ユニットテスト**
  `lib/utils/pnl.test.ts` を `TECH_DESIGN.md § 7-2` のコードで作成。日本株の損益計算・米国株の円換算・価格データなし時のフォールバックをテスト  
  → ✓ `npm run test` で 3ケース以上が pass

- [ ] **[T-55] バリデーションスキーマのユニットテスト**
  `lib/validations/holding.test.ts` を `TECH_DESIGN.md § 7-3` のコードで作成。正常ケース・不正銘柄コード・保有数ゼロ・負の取得単価をテスト  
  → ✓ 5ケース以上が pass

- [ ] **[T-56] API Route のモックテスト**
  `app/api/holdings/route.test.ts` を `TECH_DESIGN.md § 7-4` のコードで作成。Supabase を `vi.mock` でモックし、正常系 201・バリデーションエラー 422 をテスト  
  → ✓ 2ケース以上が pass

---

## Phase 15: デプロイ（Day 11 + Day 14）

- [ ] **[T-57] Vercel プロジェクト作成 + 初回デプロイ**
  Vercel に GitHub リポジトリを連携してプロジェクト作成。ビルドが成功することを確認（環境変数は次タスクで設定）  
  → ✓ Vercel ダッシュボードでビルドが green になる（ただし動作はまだ不完全）

- [ ] **[T-58] Vercel 環境変数 + Supabase Redirect URL 設定**
  Vercel の Environment Variables に `.env.local` の全変数を設定。Supabase の Authentication > URL Configuration に本番 URL を追加（`Redirect URLs`）  
  → ✓ 本番 URL でログインが完了する

- [ ] **[T-59] Google OAuth 本番設定**
  Google Cloud Console で本番ドメインを OAuth Redirect URI に追加。Supabase の Google プロバイダー設定を更新  
  → ✓ 本番で Google ログインが動く

- [ ] **[T-60] 本番環境での全機能通しテスト**
  本番 URL でユーザー登録 → ポートフォリオ追加 → 銘柄追加 → ダッシュボード確認 → AI チャットのフローを手動で通す  
  → ✓ 全ステップでエラーなし

---

## Phase 16: 仕上げ・品質確認（Day 14）

- [ ] **[T-61] `npm run type-check` + `npm run lint` を全通し**
  TypeScript エラーと ESLint エラーをすべて解消。`any` 型が残っていないことを確認  
  → ✓ 両コマンドがエラーなしで完了

- [ ] **[T-62] 法的免責表示の最終確認**
  フッター・チャット画面・AI 応答内に免責文が適切に表示されているか全ページで確認。免責文が抜けているページがあれば追加  
  → ✓ 全ページのフッターに免責文がある

- [ ] **[T-63] README.md 作成**
  プロジェクトの概要・ローカル起動手順（`npm install` → `.env.local` 設定 → `npm run dev`）・デプロイ手順を記載  
  → ✓ README を見ながら初回セットアップが完了できる

---

## タスク集計

| フェーズ | タスク数 | 目安時間 |
|---------|---------|---------|
| Phase 1: セットアップ | T-01〜04 | 2h |
| Phase 2: 型定義 | T-05〜07 | 1.5h |
| Phase 3: DB | T-08〜10 | 1.5h |
| Phase 4: 認証 | T-11〜15 | 2.5h |
| Phase 5: API 共通基盤 | T-16〜18 | 1.5h |
| Phase 6: ポートフォリオ API | T-19〜23 | 2.5h |
| Phase 7: 株価取得 | T-24〜27 | 2h |
| Phase 8: レイアウト共通 UI | T-28〜30 | 1.5h |
| Phase 9: ポートフォリオ UI | T-31〜34 | 2h |
| Phase 10: ダッシュボード UI | T-35〜38 | 2h |
| Phase 11: AI チャット Backend | T-39〜42 | 2h |
| Phase 12: AI チャット Frontend | T-43〜47 | 2.5h |
| Phase 13: ポリッシュ | T-48〜52 | 2.5h |
| Phase 14: テスト | T-53〜56 | 2h |
| Phase 15: デプロイ | T-57〜60 | 2h |
| Phase 16: 仕上げ | T-61〜63 | 1.5h |
| **合計** | **63タスク** | **≈ 31.5h** |

---

## Claude Code 利用ヒント

各タスクは以下のような指示でClaude Codeに渡すと効率的です：

```
「TECH_DESIGN.md の § X-X のコードを参考に、
[ファイルパス] を実装してください。
完了後は tsc --noEmit でエラーがないことを確認してください。」
```

**ブロックしやすいポイント:**
- T-26: Yahoo Finance JP の URL が変わっている場合がある → `query2.finance.yahoo.com` を試す
- T-42: SSE ストリーミングの Content-Type が正しくないと `useChat` がパースできない → `text/event-stream` を必ず設定
- T-57: Vercel ビルド時に `NEXT_PUBLIC_*` 以外の環境変数が undefined になる → T-58 を先にやると良い
