# API設計 — KabuAI（Next.js App Router）

---

## 設計方針

- Next.js App Router の **Route Handlers** (`app/api/*/route.ts`) を使用
- 認証: Supabase Auth の `getUser()` でサーバーサイド検証
- レスポンス形式: JSON（チャットのみ SSE ストリーム）
- エラーコード: HTTP 標準ステータスコードに準拠
- バリデーション: Zod スキーマ

---

## 認証ミドルウェア

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'

// 保護対象パス: /dashboard, /portfolio, /chat, /api/*
const PROTECTED_PATHS = ['/dashboard', '/portfolio', '/chat', '/api/']

export async function middleware(request: NextRequest) {
  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user && PROTECTED_PATHS.some(p => request.nextUrl.pathname.startsWith(p))) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
}
```

---

## API エンドポイント一覧

| メソッド | パス | 機能 | 認証 |
|---------|------|------|------|
| GET | `/api/portfolios` | ポートフォリオ一覧取得 | 必須 |
| POST | `/api/portfolios` | ポートフォリオ作成 | 必須 |
| GET | `/api/portfolios/[id]` | ポートフォリオ詳細 | 必須 |
| PATCH | `/api/portfolios/[id]` | ポートフォリオ更新 | 必須 |
| DELETE | `/api/portfolios/[id]` | ポートフォリオ削除 | 必須 |
| GET | `/api/portfolios/[id]/holdings` | 保有銘柄一覧 | 必須 |
| POST | `/api/holdings` | 保有銘柄追加 | 必須 |
| PATCH | `/api/holdings/[id]` | 保有銘柄更新 | 必須 |
| DELETE | `/api/holdings/[id]` | 保有銘柄削除 | 必須 |
| GET | `/api/prices` | 株価・為替取得 | 必須 |
| POST | `/api/chat` | AI チャット（ストリーミング）| 必須 |

---

## 詳細仕様

### `GET /api/portfolios`

**レスポンス:**
```json
{
  "portfolios": [
    {
      "id": "uuid",
      "name": "メインポートフォリオ",
      "description": null,
      "holdingsCount": 5,
      "createdAt": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

### `POST /api/portfolios`

**リクエスト:**
```json
{
  "name": "NISA口座",
  "description": "長期積立用"
}
```

**バリデーション（Zod）:**
```typescript
const CreatePortfolioSchema = z.object({
  name: z.string().min(1).max(50),
  description: z.string().max(200).optional(),
})
```

**レスポンス（201）:**
```json
{ "id": "uuid", "name": "NISA口座" }
```

---

### `GET /api/portfolios/[id]/holdings`

**レスポンス:**
```json
{
  "holdings": [
    {
      "id": "uuid",
      "stockCode": "7203",
      "stockName": "トヨタ自動車",
      "market": "JP",
      "quantity": 100,
      "avgCost": 2050,
      "acquiredAt": "2024-01-15",
      "memo": null
    }
  ]
}
```

---

### `POST /api/holdings`

**リクエスト:**
```json
{
  "portfolioId": "uuid",
  "stockCode": "7203",
  "stockName": "トヨタ自動車",
  "market": "JP",
  "quantity": 100,
  "avgCost": 2050,
  "acquiredAt": "2024-01-15"
}
```

**バリデーション（Zod）:**
```typescript
const CreateHoldingSchema = z.object({
  portfolioId:  z.string().uuid(),
  stockCode:    z.string().regex(/^[0-9]{4}$|^[A-Z]{1,5}$/),
  stockName:    z.string().min(1).max(100),
  market:       z.enum(['JP', 'US']),
  quantity:     z.number().positive(),
  avgCost:      z.number().positive(),
  acquiredAt:   z.string().date().optional(),
})
```

**レスポンス（201）:**
```json
{ "id": "uuid" }
```

---

### `PATCH /api/holdings/[id]`

**リクエスト（部分更新可）:**
```json
{
  "quantity": 150,
  "avgCost": 2100
}
```

---

### `GET /api/prices`

**クエリパラメータ:**
```
/api/prices?codes=7203,7267,AAPL,VTI
```

**内部処理:**
```typescript
// 日本株 (codes: 4桁数字)
// → J-Quants API or Yahoo Finance JP
// 米国株 (codes: 英字)
// → Yahoo Finance US
// 為替 (USD/JPY)
// → ExchangeRate-API
// キャッシュ: Next.js revalidate = 900 (15分)
```

**レスポンス:**
```json
{
  "prices": {
    "7203":  { "price": 2315.5, "currency": "JPY", "change": 12.5, "changeRate": 0.54 },
    "AAPL":  { "price": 195.23, "currency": "USD", "change": -1.2, "changeRate": -0.61 }
  },
  "forex": {
    "USDJPY": 157.32
  },
  "fetchedAt": "2026-06-28T10:00:00Z"
}
```

---

### `POST /api/chat` — ストリーミング

**リクエスト:**
```json
{
  "sessionId": "uuid | null",
  "portfolioId": "uuid",
  "message": "トヨタは今売るべきですか？"
}
```

**内部処理フロー:**
```
1. ユーザー認証確認
2. portfolioId からポートフォリオ + 保有銘柄取得
3. 株価データ取得（/api/prices を内部コール）
4. システムプロンプト構築（ポートフォリオ情報を埋め込み）
5. Claude API へストリーミングリクエスト
6. SSE でクライアントへストリーミング転送
7. 完了後 chat_messages に保存
```

**実装:**
```typescript
// app/api/chat/route.ts
import Anthropic from '@anthropic-ai/sdk'

export async function POST(request: Request) {
  const { sessionId, portfolioId, message } = await request.json()
  
  // 認証・ポートフォリオ取得...
  
  const client = new Anthropic()
  
  const stream = client.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    system: buildSystemPrompt(portfolio, holdings, prices),
    messages: [
      ...chatHistory,
      { role: 'user', content: message }
    ],
  })
  
  // ReadableStream でクライアントへストリーミング
  return new Response(
    new ReadableStream({
      async start(controller) {
        for await (const chunk of stream) {
          if (chunk.type === 'content_block_delta') {
            controller.enqueue(
              new TextEncoder().encode(`data: ${JSON.stringify({ text: chunk.delta.text })}\n\n`)
            )
          }
        }
        controller.close()
        // メッセージ保存...
      }
    }),
    { headers: { 'Content-Type': 'text/event-stream' } }
  )
}
```

**レスポンス（SSE ストリーム）:**
```
data: {"text": "トヨタ"}
data: {"text": "自動車"}
data: {"text": "（7203）について"}
...
data: {"done": true, "sessionId": "uuid"}
```

---

## エラーハンドリング

```typescript
// 共通エラーレスポンス形式
type ErrorResponse = {
  error: string   // メッセージ
  code: string    // エラーコード (例: "UNAUTHORIZED", "NOT_FOUND")
}
```

| ケース | ステータス | code |
|--------|-----------|------|
| 未認証 | 401 | `UNAUTHORIZED` |
| 他ユーザーのデータ | 403 | `FORBIDDEN` |
| リソース不存在 | 404 | `NOT_FOUND` |
| バリデーション失敗 | 422 | `VALIDATION_ERROR` |
| 株価取得失敗 | 503 | `PRICE_FETCH_ERROR` |
| Claude API エラー | 502 | `AI_ERROR` |

---

## 外部 API 一覧

| API | 用途 | 無料枠 | フォールバック |
|-----|------|--------|-------------|
| J-Quants（日本取引所）| 日本株価 | 1年分・日足 | Yahoo Finance JP |
| Yahoo Finance（非公式）| 米国株価 | 制限なし（レート制限あり）| - |
| ExchangeRate-API | USD/JPY 為替 | 1,500 req/月 | - |
| Anthropic Claude API | AI チャット | 従量課金 | - |
