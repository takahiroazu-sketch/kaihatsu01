# CODING_RULES.md — InvestLog

**バージョン:** 1.0  
**作成日:** 2026-06-28  
**適用範囲:** src/ 配下の全TypeScriptファイル

---

## 1. TypeScript

### 必須ルール

```typescript
// ✅ 明示的な型定義
const fetchTrades = async (userId: string): Promise<Trade[]> => { ... }

// ❌ any禁止
const result: any = await fetch(...)   // → unknown を使う
const result: unknown = await fetch(...)

// ❌ as による強制キャスト禁止（型ガードを使う）
const trade = data as Trade            // NG
if (isTrade(data)) { const trade = data }  // OK

// ✅ unknown → 型ガードで絞り込む
function isTrade(value: unknown): value is Trade {
  return typeof value === 'object' && value !== null && 'id' in value
}
```

### tsconfig.json 必須設定

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

---

## 2. 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| 変数・関数 | camelCase | `fetchTrades`, `tradeId` |
| 型・インターフェース | PascalCase | `Trade`, `ApiError` |
| 定数（値が変わらない） | UPPER_SNAKE | `MAX_RETRIES` |
| コンポーネント | PascalCase | `TradeCard`, `TradeForm` |
| ファイル（コンポーネント） | PascalCase.tsx | `TradeCard.tsx` |
| ファイル（ロジック） | camelCase.ts | `handler.ts`, `pnl.ts` |
| テストファイル | `*.test.ts(x)` | `trade.test.ts` |
| Enum的な定数 | as const | `EMOTION_TAGS` |

```typescript
// ✅ Enum の代わりに as const
const TRADE_TYPES = ['BUY', 'SELL'] as const
type TradeType = typeof TRADE_TYPES[number]  // 'BUY' | 'SELL'
```

---

## 3. ファイル・モジュール

### import順序（ESLintで自動整形）

```typescript
// 1. Reactコア
import { useState, useCallback } from 'react'

// 2. 外部ライブラリ（アルファベット順）
import { z } from 'zod'
import { useForm } from 'react-hook-form'

// 3. 内部モジュール（@ エイリアス）
import { apiSuccess, apiError } from '@/lib/api/handler'
import type { Trade } from '@/types/trade'

// 4. 相対パス（同ディレクトリ）
import { TradeCard } from './TradeCard'
```

### エクスポート規則

```typescript
// ✅ named export（デフォルトより追跡しやすい）
export function TradeCard({ trade }: TradeCardProps) { ... }
export type { Trade, TradeType }

// ❌ default export禁止（Next.js page/layout は除外）
export default function TradeCard() { ... }  // NG（pageは除く）
```

---

## 4. コンポーネント

### Props型定義

```typescript
// ✅ インターフェースで型定義（ファイル内でexport）
interface TradeCardProps {
  trade: Trade
  onDelete?: (id: string) => void
}

export function TradeCard({ trade, onDelete }: TradeCardProps) {
  ...
}
```

### Server Component vs Client Component

```typescript
// Server Component（デフォルト）: データフェッチ・静的表示
// → async/await 使用可
// → 'use client' なし

// Client Component: インタラクション・フォーム・状態管理
'use client'
// → useState, useEffect, useCallback 使用
// → イベントハンドラ使用
```

### フォームの実装パターン

```typescript
// react-hook-form + Zod の組み合わせを統一
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { CreateTradeSchema, type CreateTradeInput } from '@/lib/validations/trade'

const form = useForm<CreateTradeInput>({
  resolver: zodResolver(CreateTradeSchema),
  defaultValues: { tradeType: 'BUY', market: 'JP' },
})
```

---

## 5. API Route Handler

### 共通パターン

```typescript
import { getAuthUser, apiSuccess, apiError } from '@/lib/api/handler'
import { CreateTradeSchema } from '@/lib/validations/trade'

export async function POST(request: Request): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const body: unknown = await request.json()
  const parsed = CreateTradeSchema.safeParse(body)
  if (!parsed.success) {
    return apiError(parsed.error.message, 'VALIDATION_ERROR', 422)
  }

  const { data, error } = await supabase
    .from('trades')
    .insert({ ...parsed.data, user_id: user.id })
    .select('id')
    .single()

  if (error) return apiError(error.message, 'INTERNAL_ERROR', 500)

  return apiSuccess({ id: data.id }, 201)
}
```

### ルール

- 全エンドポイントで認証チェックを最初に実施
- Zodバリデーションは必ず `safeParse` を使う（例外を投げない）
- Supabase errorは必ずチェックしてからデータを使う
- HTTPステータスコードは適切に設定する（201, 204, 401, 404, 422, 500）

---

## 6. エラーハンドリング

### API Layer

```typescript
// エラーは必ず ApiError 型で返す
type ApiError = {
  error: string
  code: ErrorCode
}

type ErrorCode =
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'VALIDATION_ERROR'
  | 'INTERNAL_ERROR'
```

### Client Layer

```typescript
// fetch のエラーハンドリング
const response = await fetch('/api/trades', { method: 'POST', body: JSON.stringify(data) })

if (!response.ok) {
  const error: ApiError = await response.json()
  // toast でユーザーに通知
  toast.error(error.error)
  return
}

const { data: trade } = await response.json()
```

### try-catch の使い方

```typescript
// ✅ 外部API・DBアクセスにはtry-catchを使う
try {
  const result = await externalApi.fetch(...)
} catch (error) {
  // error は unknown 型で受け取る
  const message = error instanceof Error ? error.message : 'Unknown error'
  return apiError(message, 'INTERNAL_ERROR', 500)
}

// ❌ try-catchで握り潰さない
try {
  ...
} catch {
  return null  // NG: エラーが消える
}
```

---

## 7. テスト

### テストファイルの配置

```
src/
├── lib/
│   ├── validations/
│   │   ├── trade.ts
│   │   └── trade.test.ts    ← 同ディレクトリに配置
│   └── utils/
│       ├── pnl.ts
│       └── pnl.test.ts
└── app/api/
    └── trades/
        ├── route.ts
        └── route.test.ts
```

### テストの書き方

```typescript
import { describe, it, expect } from 'vitest'
import { CreateTradeSchema } from './trade'

describe('CreateTradeSchema', () => {
  it('有効な日本株のBUY記録を受け入れる', () => {
    const result = CreateTradeSchema.safeParse({
      stockCode: '7203',
      stockName: 'トヨタ自動車',
      market: 'JP',
      tradeType: 'BUY',
      quantity: 100,
      price: 2500,
      tradedAt: '2026-06-28',
      reason: 'PERが割安で業績が安定している',
    })
    expect(result.success).toBe(true)
  })

  it('reasonが空文字の場合は無効', () => {
    const result = CreateTradeSchema.safeParse({ ..., reason: '' })
    expect(result.success).toBe(false)
  })
})
```

### テスト命名規則

- `describe`: テスト対象のクラス・関数名
- `it`: 「〇〇の場合、〇〇になる」の形式で日本語で書く

---

## 8. コメント

### 書いていいコメント（WHYが非自明な場合のみ）

```typescript
// Yahoo Finance は認証不要だが、User-Agentがないと503を返す
headers: { 'User-Agent': 'Mozilla/5.0' }

// Supabase RLS が trades.user_id を自動フィルタするため、
// ここで user_id の条件を追加する必要はない
const { data } = await supabase.from('trades').select('*')
```

### 書かないコメント

```typescript
// ❌ コードを読めば分かることは書かない
// ユーザーIDを取得する
const userId = user.id

// ❌ 関数名で分かることは書かない
// トレードを作成する
function createTrade() { ... }

// ❌ TODO/FIXME を放置しない（タスクに落とす）
// TODO: エラーハンドリングを追加する
```

---

## 9. DRY原則の適用

```typescript
// ✅ 重複するSupabaseクエリはヘルパー化
// src/lib/supabase/queries/trade.ts
export async function getTradeById(supabase: SupabaseClient, id: string) {
  const { data, error } = await supabase
    .from('trades')
    .select('*, reviews(*)')
    .eq('id', id)
    .single()

  if (error) throw new Error(error.message)
  return data
}

// ❌ 同じクエリを複数の Route Handler に書かない
```

---

## 10. セキュリティ

- `SUPABASE_SERVICE_ROLE_KEY` はサーバーサイドのみ。`NEXT_PUBLIC_` プレフィックスをつけない
- ユーザー入力は必ずZodで検証してからDBに渡す
- SQLインジェクション対策: 生のSQLを書かない（Supabase クライアントのみ使用）
- XSS対策: ユーザー入力の `innerHTML` への直接挿入を禁止（Reactのデフォルトエスケープを使う）
- 他ユーザーのデータアクセス: RLSを信頼しつつ、Route Handler でも所有権確認を実施（二重防御）
