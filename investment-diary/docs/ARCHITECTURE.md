# ARCHITECTURE.md — InvestLog

**バージョン:** 1.0  
**作成日:** 2026-06-28

---

## 1. 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                    Browser / Mobile                   │
│         Next.js App (RSC + Client Components)         │
└─────────────┬────────────────────────────────────────┘
              │ HTTP / SSE
┌─────────────▼────────────────────────────────────────┐
│              Next.js Route Handlers (API)             │
│         app/api/**/route.ts (サーバーサイド)          │
└──────┬───────────────────────┬───────────────────────┘
       │                       │
┌──────▼──────┐    ┌──────────▼──────────────────┐
│  Supabase   │    │   External APIs              │
│  PostgreSQL │    │  - Anthropic Claude (Phase2) │
│  Auth (JWT) │    │  - Yahoo Finance  (Phase3)   │
└─────────────┘    └─────────────────────────────┘
```

---

## 2. ディレクトリ構成

```
investment-diary/
├── docs/                          # 設計ドキュメント
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── TASKS.md
│   └── CODING_RULES.md
│
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── (auth)/                # Route Group: 認証不要
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (app)/                 # Route Group: 認証必須
│   │   │   ├── layout.tsx         # 共通レイアウト（サイドバー）
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── trades/
│   │   │   │   ├── page.tsx       # 一覧
│   │   │   │   ├── new/page.tsx   # 新規作成
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx   # 詳細・編集
│   │   │   │       └── review/page.tsx
│   │   │   └── analysis/page.tsx  # Phase 2
│   │   ├── api/
│   │   │   ├── trades/
│   │   │   │   ├── route.ts       # GET, POST
│   │   │   │   └── [id]/route.ts  # GET, PATCH, DELETE
│   │   │   ├── reviews/
│   │   │   │   └── [tradeId]/route.ts
│   │   │   └── analysis/route.ts  # Phase 2
│   │   ├── layout.tsx
│   │   └── globals.css
│   │
│   ├── components/
│   │   ├── ui/                    # shadcn/ui (自動生成)
│   │   ├── trade/
│   │   │   ├── TradeForm.tsx
│   │   │   ├── TradeCard.tsx
│   │   │   └── TradeList.tsx
│   │   ├── review/
│   │   │   └── ReviewForm.tsx
│   │   ├── dashboard/
│   │   │   └── RecentTrades.tsx
│   │   └── layout/
│   │       ├── Sidebar.tsx
│   │       ├── Header.tsx
│   │       └── Footer.tsx         # 免責表示
│   │
│   ├── lib/
│   │   ├── supabase/
│   │   │   ├── client.ts          # ブラウザ用クライアント
│   │   │   ├── server.ts          # サーバー用クライアント
│   │   │   └── admin.ts           # service_role (サーバーのみ)
│   │   ├── api/
│   │   │   └── handler.ts         # 共通レスポンスヘルパー
│   │   ├── validations/
│   │   │   ├── trade.ts           # Zodスキーマ
│   │   │   └── review.ts
│   │   └── utils/
│   │       └── pnl.ts             # 損益計算
│   │
│   ├── types/
│   │   ├── trade.ts
│   │   ├── review.ts
│   │   └── api.ts
│   │
│   └── hooks/
│       ├── useTrades.ts
│       └── useReview.ts
│
├── supabase/
│   └── migrations/
│       └── 001_initial.sql
│
├── middleware.ts
├── next.config.ts
├── tsconfig.json                  # strict: true
└── vitest.config.ts
```

---

## 3. Clean Architecture レイヤー

```
┌────────────────────────────────────────────┐
│  Presentation Layer                         │
│  app/(app)/**  + components/**             │
│  - React Server Components                 │
│  - Client Components (フォーム/インタラクション)│
└────────────────────┬───────────────────────┘
                     │ fetch / Server Action
┌────────────────────▼───────────────────────┐
│  Application Layer                          │
│  app/api/**/route.ts                        │
│  - 認証チェック                              │
│  - Zodバリデーション                         │
│  - ユースケース呼び出し                       │
└────────────────────┬───────────────────────┘
                     │
┌────────────────────▼───────────────────────┐
│  Domain Layer                               │
│  types/ + lib/utils/                        │
│  - 型定義                                   │
│  - ビジネスロジック（損益計算等）              │
└────────────────────┬───────────────────────┘
                     │
┌────────────────────▼───────────────────────┐
│  Infrastructure Layer                       │
│  lib/supabase/ + lib/api/                   │
│  - Supabaseクライアント                      │
│  - 外部API呼び出し                           │
└────────────────────────────────────────────┘
```

---

## 4. データフロー

### 売買記録作成フロー

```
TradeForm (Client Component)
  │ POST /api/trades
  ▼
app/api/trades/route.ts (Route Handler)
  │ 1. getAuthUser() → 未認証は401
  │ 2. CreateTradeSchema.safeParse(body) → 不正は422
  │ 3. supabase.from('trades').insert(...)
  │ 4. 201 + { id }
  ▼
router.push(`/trades/${id}`)
```

### 認証フロー

```
middleware.ts
  │ createServerClient() → getUser()
  │ 未認証 + 保護パス → /login?next=<path>
  │ 認証済 + /login or /register → /dashboard
  ▼
Route Handler / Page
```

---

## 5. DB設計

### ERダイアグラム

```
auth.users (Supabase管理)
    │
    └── trades (1:N)
            │
            └── reviews (1:1)
```

### trades テーブル

| カラム | 型 | 制約 |
|--------|-----|------|
| id | uuid | PK |
| user_id | uuid | FK → auth.users, NOT NULL |
| stock_code | text | NOT NULL |
| stock_name | text | NOT NULL |
| market | text | CHECK ('JP','US') |
| trade_type | text | CHECK ('BUY','SELL') |
| quantity | numeric(15,4) | NOT NULL, > 0 |
| price | numeric(15,4) | NOT NULL, > 0 |
| traded_at | date | NOT NULL |
| reason | text | NOT NULL（購入/売却理由） |
| emotion_tag | text | CHECK ('CALM','GREED','FEAR','FOMO','CONVICTION') |
| created_at | timestamptz | DEFAULT now() |
| updated_at | timestamptz | DEFAULT now() |

### reviews テーブル

| カラム | 型 | 制約 |
|--------|-----|------|
| id | uuid | PK |
| trade_id | uuid | FK → trades, UNIQUE |
| outcome | text | CHECK ('PROFIT','LOSS','EVEN') |
| good_points | text | |
| improvements | text | |
| score | integer | CHECK (1 <= score <= 5) |
| created_at | timestamptz | DEFAULT now() |
| updated_at | timestamptz | DEFAULT now() |

---

## 6. API設計

| Method | Path | 機能 | 認証 |
|--------|------|------|------|
| GET | `/api/trades` | 売買記録一覧 | 必須 |
| POST | `/api/trades` | 売買記録作成 | 必須 |
| GET | `/api/trades/[id]` | 売買記録詳細 | 必須 |
| PATCH | `/api/trades/[id]` | 売買記録更新 | 必須 |
| DELETE | `/api/trades/[id]` | 売買記録削除 | 必須 |
| GET | `/api/reviews/[tradeId]` | 振り返り取得 | 必須 |
| POST | `/api/reviews/[tradeId]` | 振り返り作成 | 必須 |
| PATCH | `/api/reviews/[tradeId]` | 振り返り更新 | 必須 |
| POST | `/api/analysis` | AI分析（Phase 2） | 必須 |

### 共通レスポンス形式

```typescript
// 成功
type ApiSuccess<T> = { data: T }

// エラー
type ApiError = {
  error: string
  code: 'UNAUTHORIZED' | 'FORBIDDEN' | 'NOT_FOUND' | 'VALIDATION_ERROR' | 'INTERNAL_ERROR'
}
```

---

## 7. 認証・セキュリティ

- **Supabase Auth:** JWT ベースのセッション管理
- **RLS:** 全テーブルで有効化。`user_id = auth.uid()` で分離
- **middleware.ts:** 保護パス (`/dashboard`, `/trades`, `/analysis`, `/api/`) を認証ガード
- **service_role:** サーバーサイドのみ使用。クライアントに露出禁止

---

## 8. テスト方針

| レイヤー | ツール | 対象 |
|----------|--------|------|
| Unit | Vitest | lib/utils/*, lib/validations/* |
| Integration | Vitest + msw | app/api/**/route.ts |
| E2E | (Phase 2以降) | Playwright |

**カバレッジ目標:** ビジネスロジック（損益計算・バリデーション）100%

---

## 9. Phase別追加設計

### Phase 2 — AI分析

```
/api/analysis (POST)
  │ 1. ユーザーの全tradeデータ取得
  │ 2. reviewデータと結合
  │ 3. Claude APIへ分析依頼（SSEストリーミング）
  │    - 勝率・利益率の数値算出はアプリ側で実施
  │    - パターン抽出のみClaudeに依頼
  └─→ SSEレスポンス
```

### Phase 3 — 株価連携

```
/api/prices?code=7203&market=JP (GET)
  │ Yahoo Finance 非公式API
  │ キャッシュ: Next.js revalidate = 900 (15分)
  │ 失敗時: { error: 'PRICE_FETCH_ERROR' }
  └─→ { price, per, pbr, roe }
```

---

## 10. 環境変数

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=     # サーバーサイドのみ

# AI (Phase 2)
ANTHROPIC_API_KEY=

# App
NEXT_PUBLIC_APP_URL=
```
