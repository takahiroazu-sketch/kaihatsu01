# 技術設計書 — KabuAI

**バージョン:** 1.0  
**作成日:** 2026-06-28  
**対象:** Next.js 15 / TypeScript / Supabase / Claude API

---

## 目次

1. [ディレクトリ構成](#1-ディレクトリ構成)
2. [コンポーネント設計](#2-コンポーネント設計)
3. [API設計](#3-api設計)
4. [DBスキーマ](#4-dbスキーマ)
5. [認証方式](#5-認証方式)
6. [エラーハンドリング](#6-エラーハンドリング)
7. [テスト方針](#7-テスト方針)

---

## 1. ディレクトリ構成

```
kabuai/
├── .env.local                    # 環境変数（git 除外）
├── .env.example                  # 環境変数テンプレート
├── next.config.ts
├── middleware.ts                 # 認証ガード
├── tailwind.config.ts
│
├── app/                          # Next.js App Router
│   ├── layout.tsx                # ルートレイアウト（フォント・メタ）
│   ├── (auth)/                   # 未認証ユーザー向けグループ
│   │   ├── layout.tsx            # 認証ページ共通レイアウト
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   ├── (app)/                    # 認証済みユーザー向けグループ
│   │   ├── layout.tsx            # サイドバー付きレイアウト
│   │   ├── dashboard/
│   │   │   ├── page.tsx          # Server Component（初期データ取得）
│   │   │   └── loading.tsx       # Skeleton UI
│   │   ├── portfolio/
│   │   │   ├── page.tsx
│   │   │   ├── loading.tsx
│   │   │   └── [holdingId]/
│   │   │       └── page.tsx      # 銘柄詳細・編集
│   │   └── chat/
│   │       ├── page.tsx
│   │       └── loading.tsx
│   └── api/                      # Route Handlers
│       ├── portfolios/
│       │   ├── route.ts          # GET / POST
│       │   └── [id]/
│       │       ├── route.ts      # GET / PATCH / DELETE
│       │       └── holdings/
│       │           └── route.ts  # GET（ポートフォリオ配下の銘柄一覧）
│       ├── holdings/
│       │   ├── route.ts          # POST
│       │   └── [id]/
│       │       └── route.ts      # PATCH / DELETE
│       ├── prices/
│       │   └── route.ts          # GET（株価・為替）
│       └── chat/
│           └── route.ts          # POST（SSE ストリーミング）
│
├── components/
│   ├── ui/                       # shadcn/ui（自動生成）
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── AppHeader.tsx
│   │   └── DisclaimerFooter.tsx  # 法的免責表示
│   ├── portfolio/
│   │   ├── HoldingCard.tsx
│   │   ├── HoldingTable.tsx
│   │   ├── AddHoldingModal.tsx
│   │   └── EditHoldingForm.tsx
│   ├── dashboard/
│   │   ├── PnLSummary.tsx        # 総資産・評価損益カード
│   │   ├── AllocationChart.tsx   # 円グラフ（Recharts）
│   │   └── HoldingTableRow.tsx
│   ├── chat/
│   │   ├── ChatWindow.tsx        # メッセージ一覧・スクロール管理
│   │   ├── MessageBubble.tsx
│   │   ├── ChatInput.tsx
│   │   └── QuickQuestions.tsx    # 定型文ボタン
│   └── shared/
│       ├── ErrorBoundary.tsx
│       ├── LoadingSkeleton.tsx
│       └── EmptyState.tsx
│
├── lib/
│   ├── supabase/
│   │   ├── client.ts             # ブラウザ用クライアント
│   │   ├── server.ts             # Server Component 用クライアント
│   │   └── admin.ts              # service_role（サーバーのみ）
│   ├── ai/
│   │   ├── claude.ts             # Anthropic SDK ラッパー
│   │   └── prompts.ts            # システムプロンプト構築
│   ├── prices/
│   │   ├── fetcher.ts            # 統合エントリポイント
│   │   ├── japan.ts              # 日本株（Yahoo Finance JP）
│   │   ├── us.ts                 # 米国株（Yahoo Finance US）
│   │   └── forex.ts              # 為替（ExchangeRate-API）
│   ├── validations/
│   │   ├── portfolio.ts          # Zod スキーマ
│   │   └── holding.ts
│   └── utils/
│       ├── currency.ts           # 通貨フォーマット
│       └── pnl.ts                # 損益計算ロジック
│
├── hooks/
│   ├── usePortfolio.ts           # SWR + ポートフォリオ CRUD
│   ├── usePrices.ts              # SWR + 株価ポーリング
│   └── useChat.ts                # SSE ストリーミング管理
│
├── stores/
│   └── uiStore.ts                # Zustand（モーダル開閉状態等）
│
├── types/
│   ├── portfolio.ts
│   ├── holding.ts
│   ├── chat.ts
│   └── api.ts
│
└── supabase/
    └── migrations/
        └── 001_initial.sql       # 初期 DB マイグレーション
```

---

## 2. コンポーネント設計

### 2-1. 型定義

```typescript
// types/portfolio.ts
export type Portfolio = {
  id: string
  userId: string
  name: string
  description: string | null
  createdAt: string
  updatedAt: string
}

// types/holding.ts
export type Market = 'JP' | 'US'

export type Holding = {
  id: string
  portfolioId: string
  stockCode: string
  stockName: string
  market: Market
  quantity: number
  avgCost: number          // 現地通貨（JPまたはUSD）
  acquiredAt: string | null
  memo: string | null
  createdAt: string
}

export type HoldingWithPnL = Holding & {
  currentPrice: number     // 現地通貨
  currentValueJPY: number  // 評価額（円換算）
  costBasisJPY: number     // 取得原価（円換算）
  pnlJPY: number           // 評価損益（円）
  pnlRate: number          // 損益率（%）
}

// types/api.ts
export type ApiSuccess<T> = { data: T; error?: never }
export type ApiError = { data?: never; error: string; code: ErrorCode }
export type ApiResult<T> = ApiSuccess<T> | ApiError

export type ErrorCode =
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'VALIDATION_ERROR'
  | 'PRICE_FETCH_ERROR'
  | 'AI_ERROR'
  | 'INTERNAL_ERROR'

export type PriceData = {
  price: number
  currency: 'JPY' | 'USD'
  change: number
  changeRate: number
}

export type PricesResponse = {
  prices: Record<string, PriceData>
  forex: { USDJPY: number }
  fetchedAt: string
}

// types/chat.ts
export type ChatRole = 'user' | 'assistant'

export type ChatMessage = {
  id: string
  sessionId: string
  role: ChatRole
  content: string
  createdAt: string
}

export type ChatSession = {
  id: string
  userId: string
  portfolioId: string | null
  title: string | null
  createdAt: string
}
```

### 2-2. コンポーネント階層

```
(app)/layout.tsx [Server]
└── AppLayout [Server]
    ├── Sidebar [Client] ← 現在パスをハイライト
    └── {children}

dashboard/page.tsx [Server] ← 初期データ SSR 取得
├── PnLSummary [Client]    ← props: { totalValueJPY, pnlJPY, pnlRate }
├── AllocationChart [Client] ← props: { holdings }
└── HoldingTable [Client]  ← props: { holdings } + usePrices() でリアルタイム更新

portfolio/page.tsx [Server]
├── AddHoldingModal [Client] ← Zustand の isOpen で制御
└── HoldingCard × N [Client] ← props: { holding }

chat/page.tsx [Client] ← 全体 Client（SSE が必要）
├── ChatWindow [Client]
│   └── MessageBubble × N
├── ChatInput [Client]
└── QuickQuestions [Client]
```

### 2-3. PnLSummary（損益サマリーカード）

```typescript
// components/dashboard/PnLSummary.tsx
'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatRate } from '@/lib/utils/currency'
import { cn } from '@/lib/utils'

type Props = {
  totalValueJPY: number
  pnlJPY: number
  pnlRate: number
}

export function PnLSummary({ totalValueJPY, pnlJPY, pnlRate }: Props) {
  const isPositive = pnlJPY >= 0

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            総評価額
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{formatCurrency(totalValueJPY)}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            評価損益
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className={cn('text-2xl font-bold', isPositive ? 'text-green-600' : 'text-red-600')}>
            {isPositive ? '+' : ''}{formatCurrency(pnlJPY)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            損益率
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className={cn('text-2xl font-bold', isPositive ? 'text-green-600' : 'text-red-600')}>
            {isPositive ? '+' : ''}{formatRate(pnlRate)}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
```

### 2-4. AddHoldingModal（銘柄追加モーダル）

```typescript
// components/portfolio/AddHoldingModal.tsx
'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { CreateHoldingSchema, type CreateHoldingInput } from '@/lib/validations/holding'
import { usePortfolio } from '@/hooks/usePortfolio'

type Props = {
  portfolioId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AddHoldingModal({ portfolioId, open, onOpenChange }: Props) {
  const { addHolding } = usePortfolio(portfolioId)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<CreateHoldingInput>({
    resolver: zodResolver(CreateHoldingSchema),
    defaultValues: {
      portfolioId,
      market: 'JP',
      quantity: undefined,
      avgCost: undefined,
    },
  })

  async function onSubmit(values: CreateHoldingInput) {
    setIsSubmitting(true)
    try {
      await addHolding(values)
      form.reset()
      onOpenChange(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>銘柄を追加</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="market"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>市場</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="JP">日本株</SelectItem>
                      <SelectItem value="US">米国株</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="stockCode"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>銘柄コード</FormLabel>
                  <FormControl>
                    <Input placeholder="例: 7203 / AAPL" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="stockName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>銘柄名</FormLabel>
                  <FormControl>
                    <Input placeholder="例: トヨタ自動車" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="quantity"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>保有数（株）</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.0001"
                        {...field}
                        onChange={e => field.onChange(e.target.valueAsNumber)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="avgCost"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>取得単価</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        {...field}
                        onChange={e => field.onChange(e.target.valueAsNumber)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="acquiredAt"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>取得日（任意）</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                キャンセル
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? '追加中...' : '追加する'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
```

### 2-5. ChatWindow（AI チャット）

```typescript
// components/chat/ChatWindow.tsx
'use client'

import { useEffect, useRef } from 'react'
import { MessageBubble } from './MessageBubble'
import { ChatInput } from './ChatInput'
import { QuickQuestions } from './QuickQuestions'
import { useChat } from '@/hooks/useChat'
import { DisclaimerBanner } from '../shared/DisclaimerBanner'

type Props = { portfolioId: string }

export function ChatWindow({ portfolioId }: Props) {
  const { messages, isStreaming, sendMessage } = useChat(portfolioId)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex h-full flex-col">
      <DisclaimerBanner />

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <QuickQuestions onSelect={sendMessage} />
        )}
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && (
          <MessageBubble
            message={{ id: 'streaming', role: 'assistant', content: '...', sessionId: '', createdAt: '' }}
            isStreaming
          />
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t p-4">
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>
    </div>
  )
}
```

### 2-6. カスタムフック

```typescript
// hooks/useChat.ts
'use client'

import { useState, useCallback } from 'react'
import type { ChatMessage } from '@/types/chat'

export function useChat(portfolioId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = useCallback(async (content: string) => {
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      sessionId: sessionId ?? '',
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsStreaming(true)

    let aiContent = ''
    const aiMsgId = crypto.randomUUID()

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, portfolioId, message: content }),
      })

      if (!res.ok) throw new Error('AI エラーが発生しました')

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const lines = decoder.decode(value).split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const json = JSON.parse(line.slice(6))

          if (json.text) {
            aiContent += json.text
            setMessages(prev => {
              const existing = prev.find(m => m.id === aiMsgId)
              if (existing) {
                return prev.map(m => m.id === aiMsgId ? { ...m, content: aiContent } : m)
              }
              return [...prev, {
                id: aiMsgId,
                sessionId: sessionId ?? '',
                role: 'assistant' as const,
                content: aiContent,
                createdAt: new Date().toISOString(),
              }]
            })
          }

          if (json.done && json.sessionId) {
            setSessionId(json.sessionId)
          }
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        sessionId: sessionId ?? '',
        role: 'assistant',
        content: 'エラーが発生しました。もう一度お試しください。',
        createdAt: new Date().toISOString(),
      }])
    } finally {
      setIsStreaming(false)
    }
  }, [portfolioId, sessionId])

  return { messages, isStreaming, sendMessage }
}
```

```typescript
// hooks/usePrices.ts
import useSWR from 'swr'
import type { PricesResponse } from '@/types/api'

const fetcher = (url: string) => fetch(url).then(r => r.json())

export function usePrices(stockCodes: string[]) {
  const query = stockCodes.join(',')
  const { data, error, isLoading } = useSWR<PricesResponse>(
    stockCodes.length > 0 ? `/api/prices?codes=${query}` : null,
    fetcher,
    { refreshInterval: 15 * 60 * 1000 }  // 15分ごとに再取得
  )

  return {
    prices: data?.prices ?? {},
    forex: data?.forex ?? { USDJPY: 150 },
    isLoading,
    isError: !!error,
  }
}
```

### 2-7. ユーティリティ

```typescript
// lib/utils/currency.ts
export function formatCurrency(value: number, currency: 'JPY' | 'USD' = 'JPY'): string {
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency,
    maximumFractionDigits: currency === 'JPY' ? 0 : 2,
  }).format(value)
}

export function formatRate(rate: number): string {
  return `${rate >= 0 ? '+' : ''}${rate.toFixed(2)}%`
}

// lib/utils/pnl.ts
import type { Holding, HoldingWithPnL, PricesResponse } from '@/types'

export function enrichHoldingsWithPnL(
  holdings: Holding[],
  { prices, forex }: PricesResponse
): HoldingWithPnL[] {
  return holdings.map(h => {
    const priceData = prices[h.stockCode]
    const currentPrice = priceData?.price ?? h.avgCost
    const usdJpy = forex.USDJPY

    const toJPY = (amount: number) =>
      h.market === 'US' ? amount * usdJpy : amount

    const currentValueJPY = toJPY(currentPrice * h.quantity)
    const costBasisJPY = toJPY(h.avgCost * h.quantity)
    const pnlJPY = currentValueJPY - costBasisJPY
    const pnlRate = costBasisJPY > 0 ? (pnlJPY / costBasisJPY) * 100 : 0

    return { ...h, currentPrice, currentValueJPY, costBasisJPY, pnlJPY, pnlRate }
  })
}

export function calcPortfolioSummary(holdings: HoldingWithPnL[]) {
  const totalValueJPY = holdings.reduce((sum, h) => sum + h.currentValueJPY, 0)
  const totalCostJPY  = holdings.reduce((sum, h) => sum + h.costBasisJPY, 0)
  const pnlJPY = totalValueJPY - totalCostJPY
  const pnlRate = totalCostJPY > 0 ? (pnlJPY / totalCostJPY) * 100 : 0
  return { totalValueJPY, pnlJPY, pnlRate }
}
```

---

## 3. API設計

### 3-1. ルートハンドラー基盤

```typescript
// lib/api/handler.ts  ← 全ルートで使う共通ラッパー
import { createServerClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'
import type { ApiResult, ErrorCode } from '@/types/api'

export function apiError(message: string, code: ErrorCode, status: number) {
  return NextResponse.json<ApiResult<never>>({ error: message, code }, { status })
}

export function apiSuccess<T>(data: T, status = 200) {
  return NextResponse.json<ApiResult<T>>({ data }, { status })
}

export async function getAuthUser() {
  const supabase = await createServerClient()
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error || !user) return null
  return user
}
```

### 3-2. ポートフォリオ API

```typescript
// app/api/portfolios/route.ts
import { NextRequest } from 'next/server'
import { z } from 'zod'
import { createServerClient } from '@/lib/supabase/server'
import { apiError, apiSuccess, getAuthUser } from '@/lib/api/handler'

const CreatePortfolioSchema = z.object({
  name: z.string().min(1).max(50),
  description: z.string().max(200).optional(),
})

export async function GET() {
  const user = await getAuthUser()
  if (!user) return apiError('認証が必要です', 'UNAUTHORIZED', 401)

  const supabase = await createServerClient()
  const { data, error } = await supabase
    .from('portfolios')
    .select('*, holdings(count)')
    .eq('user_id', user.id)
    .order('created_at', { ascending: true })

  if (error) return apiError('取得に失敗しました', 'INTERNAL_ERROR', 500)
  return apiSuccess(data)
}

export async function POST(req: NextRequest) {
  const user = await getAuthUser()
  if (!user) return apiError('認証が必要です', 'UNAUTHORIZED', 401)

  const body = await req.json()
  const parsed = CreatePortfolioSchema.safeParse(body)
  if (!parsed.success) {
    return apiError(parsed.error.message, 'VALIDATION_ERROR', 422)
  }

  const supabase = await createServerClient()
  const { data, error } = await supabase
    .from('portfolios')
    .insert({ ...parsed.data, user_id: user.id })
    .select()
    .single()

  if (error) return apiError('作成に失敗しました', 'INTERNAL_ERROR', 500)
  return apiSuccess(data, 201)
}
```

### 3-3. 保有銘柄 API

```typescript
// app/api/holdings/route.ts
import { NextRequest } from 'next/server'
import { createServerClient } from '@/lib/supabase/server'
import { apiError, apiSuccess, getAuthUser } from '@/lib/api/handler'
import { CreateHoldingSchema } from '@/lib/validations/holding'

export async function POST(req: NextRequest) {
  const user = await getAuthUser()
  if (!user) return apiError('認証が必要です', 'UNAUTHORIZED', 401)

  const body = await req.json()
  const parsed = CreateHoldingSchema.safeParse(body)
  if (!parsed.success) {
    return apiError(parsed.error.message, 'VALIDATION_ERROR', 422)
  }

  const supabase = await createServerClient()

  // ポートフォリオの所有者確認
  const { data: portfolio } = await supabase
    .from('portfolios')
    .select('id')
    .eq('id', parsed.data.portfolioId)
    .eq('user_id', user.id)
    .single()

  if (!portfolio) return apiError('ポートフォリオが見つかりません', 'FORBIDDEN', 403)

  const { data, error } = await supabase
    .from('holdings')
    .insert({
      portfolio_id: parsed.data.portfolioId,
      stock_code: parsed.data.stockCode,
      stock_name: parsed.data.stockName,
      market: parsed.data.market,
      quantity: parsed.data.quantity,
      avg_cost: parsed.data.avgCost,
      acquired_at: parsed.data.acquiredAt ?? null,
    })
    .select()
    .single()

  if (error) {
    if (error.code === '23505') {
      return apiError('この銘柄はすでに登録されています', 'VALIDATION_ERROR', 422)
    }
    return apiError('追加に失敗しました', 'INTERNAL_ERROR', 500)
  }

  return apiSuccess(data, 201)
}
```

### 3-4. 株価取得 API

```typescript
// app/api/prices/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { fetchPrices } from '@/lib/prices/fetcher'
import { apiError, apiSuccess, getAuthUser } from '@/lib/api/handler'

export async function GET(req: NextRequest) {
  const user = await getAuthUser()
  if (!user) return apiError('認証が必要です', 'UNAUTHORIZED', 401)

  const codes = req.nextUrl.searchParams.get('codes')
  if (!codes) return apiError('codes パラメータが必要です', 'VALIDATION_ERROR', 422)

  const stockCodes = codes.split(',').filter(Boolean).slice(0, 50) // 上限50銘柄

  try {
    const result = await fetchPrices(stockCodes)
    return NextResponse.json(result, {
      headers: { 'Cache-Control': 'private, max-age=900' }
    })
  } catch (err) {
    return apiError('株価データの取得に失敗しました', 'PRICE_FETCH_ERROR', 503)
  }
}
```

```typescript
// lib/prices/fetcher.ts
import { fetchJapanPrices } from './japan'
import { fetchUSPrices } from './us'
import { fetchForex } from './forex'
import type { PricesResponse } from '@/types/api'

export async function fetchPrices(codes: string[]): Promise<PricesResponse> {
  const jpCodes = codes.filter(c => /^\d{4}$/.test(c))
  const usCodes = codes.filter(c => /^[A-Z]{1,5}$/.test(c))

  const [jpPrices, usPrices, forex] = await Promise.allSettled([
    jpCodes.length > 0 ? fetchJapanPrices(jpCodes) : Promise.resolve({}),
    usCodes.length > 0 ? fetchUSPrices(usCodes)   : Promise.resolve({}),
    fetchForex(),
  ])

  return {
    prices: {
      ...(jpPrices.status === 'fulfilled' ? jpPrices.value : {}),
      ...(usPrices.status === 'fulfilled' ? usPrices.value : {}),
    },
    forex: forex.status === 'fulfilled' ? forex.value : { USDJPY: 150 },
    fetchedAt: new Date().toISOString(),
  }
}
```

```typescript
// lib/prices/japan.ts
import type { PriceData } from '@/types/api'

export async function fetchJapanPrices(
  codes: string[]
): Promise<Record<string, PriceData>> {
  const results: Record<string, PriceData> = {}

  await Promise.all(
    codes.map(async code => {
      try {
        const ticker = `${code}.T`
        const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=2d`
        const res = await fetch(url, { next: { revalidate: 900 } })
        const json = await res.json()

        const meta = json.chart?.result?.[0]?.meta
        if (!meta) return

        results[code] = {
          price: meta.regularMarketPrice ?? meta.previousClose,
          currency: 'JPY',
          change: (meta.regularMarketPrice ?? 0) - (meta.previousClose ?? 0),
          changeRate: ((meta.regularMarketPrice - meta.previousClose) / meta.previousClose) * 100,
        }
      } catch {
        // 個別銘柄の失敗は無視して続行
      }
    })
  )

  return results
}
```

### 3-5. AI チャット API（ストリーミング）

```typescript
// app/api/chat/route.ts
import { NextRequest } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { createServerClient } from '@/lib/supabase/server'
import { apiError, getAuthUser } from '@/lib/api/handler'
import { buildSystemPrompt } from '@/lib/ai/prompts'
import { fetchPrices } from '@/lib/prices/fetcher'
import { enrichHoldingsWithPnL } from '@/lib/utils/pnl'

const anthropic = new Anthropic()

export async function POST(req: NextRequest) {
  const user = await getAuthUser()
  if (!user) return apiError('認証が必要です', 'UNAUTHORIZED', 401)

  const { sessionId, portfolioId, message } = await req.json()

  const supabase = await createServerClient()

  // ポートフォリオ + 保有銘柄を取得
  const { data: portfolio } = await supabase
    .from('portfolios')
    .select('*')
    .eq('id', portfolioId)
    .eq('user_id', user.id)
    .single()

  if (!portfolio) return apiError('ポートフォリオが見つかりません', 'FORBIDDEN', 403)

  const { data: holdings } = await supabase
    .from('holdings')
    .select('*')
    .eq('portfolio_id', portfolioId)

  // 株価取得して損益計算
  const codes = (holdings ?? []).map(h => h.stock_code)
  const priceData = await fetchPrices(codes)
  const holdingsWithPnL = enrichHoldingsWithPnL(holdings ?? [], priceData)

  // チャット履歴取得
  let currentSessionId = sessionId
  let chatHistory: Anthropic.MessageParam[] = []

  if (currentSessionId) {
    const { data: msgs } = await supabase
      .from('chat_messages')
      .select('role, content')
      .eq('session_id', currentSessionId)
      .order('created_at', { ascending: true })
      .limit(20)

    chatHistory = (msgs ?? []).map(m => ({
      role: m.role as 'user' | 'assistant',
      content: m.content,
    }))
  } else {
    // 新規セッション作成
    const { data: session } = await supabase
      .from('chat_sessions')
      .insert({ user_id: user.id, portfolio_id: portfolioId })
      .select()
      .single()
    currentSessionId = session?.id
  }

  // ユーザーメッセージを DB 保存
  await supabase.from('chat_messages').insert({
    session_id: currentSessionId,
    role: 'user',
    content: message,
  })

  // ストリーミングレスポンス
  let fullResponse = ''

  const stream = new ReadableStream({
    async start(controller) {
      const encode = (data: object) =>
        controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(data)}\n\n`))

      try {
        const stream = anthropic.messages.stream({
          model: 'claude-sonnet-4-6',
          max_tokens: 1024,
          system: buildSystemPrompt(portfolio, holdingsWithPnL, priceData.forex),
          messages: [
            ...chatHistory,
            { role: 'user', content: message },
          ],
        })

        for await (const event of stream) {
          if (
            event.type === 'content_block_delta' &&
            event.delta.type === 'text_delta'
          ) {
            fullResponse += event.delta.text
            encode({ text: event.delta.text })
          }
        }

        // AI 応答を DB 保存
        await supabase.from('chat_messages').insert({
          session_id: currentSessionId,
          role: 'assistant',
          content: fullResponse,
        })

        encode({ done: true, sessionId: currentSessionId })
      } catch (err) {
        encode({ error: 'AI エラーが発生しました' })
      } finally {
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
```

### 3-6. AI プロンプト設計

```typescript
// lib/ai/prompts.ts
import type { Portfolio } from '@/types/portfolio'
import type { HoldingWithPnL } from '@/types/holding'
import { formatCurrency, formatRate } from '@/lib/utils/currency'

export function buildSystemPrompt(
  portfolio: Portfolio,
  holdings: HoldingWithPnL[],
  forex: { USDJPY: number }
): string {
  const totalValueJPY = holdings.reduce((s, h) => s + h.currentValueJPY, 0)
  const totalCostJPY  = holdings.reduce((s, h) => s + h.costBasisJPY, 0)
  const pnlJPY = totalValueJPY - totalCostJPY
  const pnlRate = totalCostJPY > 0 ? (pnlJPY / totalCostJPY) * 100 : 0

  const holdingsSummary = holdings
    .map(h => [
      `【${h.stockName}（${h.stockCode}/${h.market}）】`,
      `  保有数: ${h.quantity}株`,
      `  取得単価: ${formatCurrency(h.avgCost, h.market === 'US' ? 'USD' : 'JPY')}`,
      `  現在値: ${formatCurrency(h.currentPrice, h.market === 'US' ? 'USD' : 'JPY')}`,
      `  評価損益: ${formatCurrency(h.pnlJPY)}（${formatRate(h.pnlRate)}）`,
    ].join('\n'))
    .join('\n\n')

  return `あなたは個人投資家の投資分析をサポートするAIアシスタントです。

## 行動ガイドライン（最優先）

1. **根拠のない銘柄推奨を絶対に行わない**
   - ユーザーが保有していない銘柄を推奨する場合は、必ず数値的根拠（PER・ROE・配当利回り・騰落率等）を明示すること
   - 「なんとなく良さそう」「話題だから」という理由での推奨は禁止

2. **分析には必ず根拠を添える**
   - 具体的な数値・比率・業界比較を使って説明する
   - 不確実な情報は「〜とされています」等の表現で曖昧さを示す

3. **免責の徹底**
   - 売買判断に関わる回答の末尾には必ず「投資判断はご自身の責任でお願いします」を付ける

4. **日本語で回答する**

## ユーザーのポートフォリオ情報（現在時刻取得）

ポートフォリオ名: ${portfolio.name}
総評価額: ${formatCurrency(totalValueJPY)}
評価損益: ${formatCurrency(pnlJPY)}（${formatRate(pnlRate)}）
USD/JPY: ${forex.USDJPY}円

### 保有銘柄

${holdingsSummary}

上記の情報を踏まえて、ユーザーの質問に具体的かつ誠実に回答してください。`
}
```

---

## 4. DBスキーマ

### 4-1. マイグレーションファイル

```sql
-- supabase/migrations/001_initial.sql

-- =============================================
-- Extension
-- =============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- updated_at 自動更新トリガー関数
-- =============================================
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- portfolios
-- =============================================
CREATE TABLE portfolios (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name        TEXT        NOT NULL DEFAULT 'メインポートフォリオ'
                          CHECK (char_length(name) BETWEEN 1 AND 50),
  description TEXT        CHECK (char_length(description) <= 200),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);

CREATE TRIGGER trg_portfolios_updated_at
  BEFORE UPDATE ON portfolios
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY "portfolios: users manage own"
  ON portfolios FOR ALL
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- =============================================
-- holdings
-- =============================================
CREATE TABLE holdings (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id  UUID        NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  stock_code    TEXT        NOT NULL
                            CHECK (
                              stock_code ~ '^\d{4}$'        -- 日本株
                              OR stock_code ~ '^[A-Z]{1,5}$' -- 米国株
                            ),
  stock_name    TEXT        NOT NULL CHECK (char_length(stock_name) BETWEEN 1 AND 100),
  market        TEXT        NOT NULL CHECK (market IN ('JP', 'US')),
  quantity      NUMERIC(15,4) NOT NULL CHECK (quantity > 0),
  avg_cost      NUMERIC(15,4) NOT NULL CHECK (avg_cost > 0),
  acquired_at   DATE,
  memo          TEXT        CHECK (char_length(memo) <= 500),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (portfolio_id, stock_code)
);

CREATE INDEX idx_holdings_portfolio_id ON holdings(portfolio_id);
CREATE INDEX idx_holdings_stock_code   ON holdings(stock_code);

CREATE TRIGGER trg_holdings_updated_at
  BEFORE UPDATE ON holdings
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "holdings: users manage own"
  ON holdings FOR ALL
  USING (
    portfolio_id IN (
      SELECT id FROM portfolios WHERE user_id = auth.uid()
    )
  )
  WITH CHECK (
    portfolio_id IN (
      SELECT id FROM portfolios WHERE user_id = auth.uid()
    )
  );

-- =============================================
-- chat_sessions
-- =============================================
CREATE TABLE chat_sessions (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  portfolio_id  UUID        REFERENCES portfolios(id) ON DELETE SET NULL,
  title         TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);

ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "chat_sessions: users manage own"
  ON chat_sessions FOR ALL
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- =============================================
-- chat_messages
-- =============================================
CREATE TABLE chat_messages (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID        NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
  content     TEXT        NOT NULL CHECK (char_length(content) > 0),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_id_created ON chat_messages(session_id, created_at);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "chat_messages: users manage own"
  ON chat_messages FOR ALL
  USING (
    session_id IN (
      SELECT id FROM chat_sessions WHERE user_id = auth.uid()
    )
  )
  WITH CHECK (
    session_id IN (
      SELECT id FROM chat_sessions WHERE user_id = auth.uid()
    )
  );
```

### 4-2. TypeScript 型とDBカラムのマッピング

```typescript
// lib/supabase/database.types.ts（supabase gen types で自動生成後に確認）
export type Database = {
  public: {
    Tables: {
      portfolios: {
        Row: {
          id: string
          user_id: string
          name: string
          description: string | null
          created_at: string
          updated_at: string
        }
        Insert: Omit<Database['public']['Tables']['portfolios']['Row'], 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['portfolios']['Insert']>
      }
      holdings: {
        Row: {
          id: string
          portfolio_id: string
          stock_code: string
          stock_name: string
          market: 'JP' | 'US'
          quantity: number
          avg_cost: number
          acquired_at: string | null
          memo: string | null
          created_at: string
          updated_at: string
        }
        Insert: Omit<Database['public']['Tables']['holdings']['Row'], 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['holdings']['Insert']>
      }
      chat_sessions: {
        Row: {
          id: string
          user_id: string
          portfolio_id: string | null
          title: string | null
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['chat_sessions']['Row'], 'id' | 'created_at'>
        Update: Partial<Database['public']['Tables']['chat_sessions']['Insert']>
      }
      chat_messages: {
        Row: {
          id: string
          session_id: string
          role: 'user' | 'assistant'
          content: string
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['chat_messages']['Row'], 'id' | 'created_at'>
        Update: never
      }
    }
  }
}
```

---

## 5. 認証方式

### 5-1. 全体フロー

```
ブラウザ ──[GET /dashboard]──▶ middleware.ts
                                    │
                          Supabase Cookie からセッション確認
                                    │
                        ┌──────────┴─────────┐
                     未認証                  認証済み
                        │                       │
              redirect /login           そのまま通過
                        │
              ログインフォーム送信
                        │
               Supabase Auth API
                        │
                  Cookie にセッション保存
                        │
               redirect /dashboard
```

### 5-2. Supabase クライアント

```typescript
// lib/supabase/client.ts — ブラウザ用（シングルトン）
import { createBrowserClient } from '@supabase/ssr'
import type { Database } from './database.types'

let client: ReturnType<typeof createBrowserClient<Database>> | null = null

export function getSupabaseBrowserClient() {
  if (!client) {
    client = createBrowserClient<Database>(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  }
  return client
}
```

```typescript
// lib/supabase/server.ts — Server Component / Route Handler 用
import { createServerClient as _createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { Database } from './database.types'

export async function createServerClient() {
  const cookieStore = await cookies()

  return _createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        },
      },
    }
  )
}
```

### 5-3. ミドルウェア

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

const AUTH_ROUTES = ['/login', '/register']
const PUBLIC_ROUTES = ['/', '/login', '/register']

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()
  const { pathname } = request.nextUrl

  // 認証済みユーザーがログインページにアクセス → ダッシュボードへ
  if (user && AUTH_ROUTES.includes(pathname)) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // 未認証ユーザーが保護ルートにアクセス → ログインへ
  if (!user && !PUBLIC_ROUTES.includes(pathname)) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('next', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return supabaseResponse
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
}
```

### 5-4. ログインフォーム

```typescript
// app/(auth)/login/page.tsx
'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { getSupabaseBrowserClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const supabase = getSupabaseBrowserClient()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleEmailLogin(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    const { error } = await supabase.auth.signInWithPassword({ email, password })

    if (error) {
      setError('メールアドレスまたはパスワードが正しくありません')
    } else {
      const next = searchParams.get('next') ?? '/dashboard'
      router.push(next)
      router.refresh()
    }

    setLoading(false)
  }

  async function handleGoogleLogin() {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${location.origin}/auth/callback` },
    })
  }

  return (
    <div className="mx-auto w-full max-w-sm space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">KabuAI</h1>
        <p className="text-muted-foreground text-sm mt-1">ログイン</p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleEmailLogin} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">メールアドレス</Label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">パスワード</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'ログイン中...' : 'ログイン'}
        </Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">または</span>
        </div>
      </div>

      <Button variant="outline" className="w-full" onClick={handleGoogleLogin}>
        Google でログイン
      </Button>
    </div>
  )
}
```

---

## 6. エラーハンドリング

### 6-1. エラー分類と対応

| レイヤー | エラー種別 | 対応 |
|---------|-----------|------|
| API Route | 認証エラー | 401 + リダイレクト |
| API Route | バリデーション | 422 + フィールドエラー表示 |
| API Route | 株価取得失敗 | 503 + キャッシュ値フォールバック |
| API Route | DB エラー | 500 + ログ記録 |
| Client | ネットワークエラー | トースト通知 + 再試行ボタン |
| Client | AI ストリームエラー | インラインメッセージ |

### 6-2. カスタムエラークラス

```typescript
// lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500
  ) {
    super(message)
    this.name = 'AppError'
  }
}

export class PriceFetchError extends AppError {
  constructor(stockCode: string, cause?: unknown) {
    super(`株価取得失敗: ${stockCode}`, 'PRICE_FETCH_ERROR', 503)
    this.cause = cause
  }
}

export class PortfolioNotFoundError extends AppError {
  constructor(id: string) {
    super(`ポートフォリオが見つかりません: ${id}`, 'NOT_FOUND', 404)
  }
}
```

### 6-3. React Error Boundary

```typescript
// components/shared/ErrorBoundary.tsx
'use client'

import { Component, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'

type Props = { children: ReactNode; fallback?: ReactNode }
type State = { hasError: boolean; error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="flex flex-col items-center gap-4 p-8">
          <p className="text-destructive font-medium">予期しないエラーが発生しました</p>
          <p className="text-muted-foreground text-sm">{this.state.error?.message}</p>
          <Button onClick={() => this.setState({ hasError: false, error: null })}>
            再試行
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
```

### 6-4. グローバルトースト通知

```typescript
// lib/toast.ts — Sonner を使用
import { toast } from 'sonner'

export const notify = {
  success: (message: string) => toast.success(message),
  error: (message: string) =>
    toast.error(message, { duration: 5000, action: { label: '閉じる', onClick: () => {} } }),
  loading: (message: string) => toast.loading(message),
}

// 使用例
// notify.error('株価データの取得に失敗しました')
// notify.success('銘柄を追加しました')
```

### 6-5. fetch ラッパー（クライアント用）

```typescript
// lib/fetcher.ts
import { notify } from './toast'

type FetchOptions = RequestInit & { silent?: boolean }

export async function apiFetch<T>(
  url: string,
  options: FetchOptions = {}
): Promise<T> {
  const { silent = false, ...fetchOptions } = options

  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...fetchOptions,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const message = body.error ?? `エラーが発生しました (${res.status})`

    if (!silent) notify.error(message)

    if (res.status === 401) {
      window.location.href = '/login'
    }

    throw new Error(message)
  }

  return res.json()
}
```

---

## 7. テスト方針

### 7-1. テストピラミッド（MVP）

```
              /\
             /E2E\        Playwright — 主要フロー 3〜5本のみ
            /──────\
           / 結合   \     Vitest — API Route Handler
          /──────────\
         /  単体テスト \   Vitest — utils / prompts / validation
        /──────────────\
```

**MVP での優先度:**
- 単体テスト（utils）: **必須** — 損益計算バグは直接損害になる
- バリデーション: **必須** — 不正データの DB 混入防止
- API 結合テスト: **推奨** — 認証・RLS 確認
- E2E: **最小限** — ログイン + ポートフォリオ追加 + チャットの3本

### 7-2. 損益計算ユニットテスト

```typescript
// lib/utils/pnl.test.ts
import { describe, it, expect } from 'vitest'
import { enrichHoldingsWithPnL, calcPortfolioSummary } from './pnl'
import type { Holding } from '@/types/holding'

const baseHolding: Holding = {
  id: '1',
  portfolioId: 'p1',
  stockCode: '7203',
  stockName: 'トヨタ自動車',
  market: 'JP',
  quantity: 100,
  avgCost: 2000,
  acquiredAt: null,
  memo: null,
  createdAt: '',
}

const mockPrices = {
  prices: {
    '7203': { price: 2200, currency: 'JPY' as const, change: 200, changeRate: 10 },
  },
  forex: { USDJPY: 150 },
  fetchedAt: '',
}

describe('enrichHoldingsWithPnL', () => {
  it('日本株の損益を正しく計算する', () => {
    const result = enrichHoldingsWithPnL([baseHolding], mockPrices)
    expect(result[0].currentValueJPY).toBe(220_000)  // 2200 × 100
    expect(result[0].costBasisJPY).toBe(200_000)      // 2000 × 100
    expect(result[0].pnlJPY).toBe(20_000)
    expect(result[0].pnlRate).toBeCloseTo(10.0)
  })

  it('米国株は USD/JPY で円換算する', () => {
    const usHolding: Holding = {
      ...baseHolding,
      id: '2',
      stockCode: 'AAPL',
      stockName: 'Apple',
      market: 'US',
      quantity: 10,
      avgCost: 180,
    }
    const prices = {
      prices: { AAPL: { price: 195, currency: 'USD' as const, change: 15, changeRate: 8.3 } },
      forex: { USDJPY: 150 },
      fetchedAt: '',
    }
    const result = enrichHoldingsWithPnL([usHolding], prices)
    expect(result[0].currentValueJPY).toBe(195 * 10 * 150)  // 292,500
    expect(result[0].costBasisJPY).toBe(180 * 10 * 150)     // 270,000
    expect(result[0].pnlJPY).toBe(22_500)
  })

  it('価格データが存在しない場合は取得単価を現在値とする', () => {
    const result = enrichHoldingsWithPnL([baseHolding], { ...mockPrices, prices: {} })
    expect(result[0].pnlJPY).toBe(0)
    expect(result[0].pnlRate).toBe(0)
  })
})

describe('calcPortfolioSummary', () => {
  it('複数銘柄の合計を正しく計算する', () => {
    const holdings = enrichHoldingsWithPnL([baseHolding], mockPrices)
    const summary = calcPortfolioSummary(holdings)
    expect(summary.totalValueJPY).toBe(220_000)
    expect(summary.pnlJPY).toBe(20_000)
    expect(summary.pnlRate).toBeCloseTo(10.0)
  })
})
```

### 7-3. バリデーションテスト

```typescript
// lib/validations/holding.test.ts
import { describe, it, expect } from 'vitest'
import { CreateHoldingSchema } from './holding'

describe('CreateHoldingSchema', () => {
  const validJP = {
    portfolioId: '550e8400-e29b-41d4-a716-446655440000',
    stockCode: '7203',
    stockName: 'トヨタ自動車',
    market: 'JP' as const,
    quantity: 100,
    avgCost: 2050,
  }

  it('正常な日本株データを受け入れる', () => {
    expect(CreateHoldingSchema.safeParse(validJP).success).toBe(true)
  })

  it('正常な米国株データを受け入れる', () => {
    const valid = { ...validJP, stockCode: 'AAPL', stockName: 'Apple', market: 'US' as const }
    expect(CreateHoldingSchema.safeParse(valid).success).toBe(true)
  })

  it('銘柄コードが不正な形式を拒否する', () => {
    const invalid = { ...validJP, stockCode: 'INVALID123' }
    expect(CreateHoldingSchema.safeParse(invalid).success).toBe(false)
  })

  it('保有数 0 を拒否する', () => {
    expect(CreateHoldingSchema.safeParse({ ...validJP, quantity: 0 }).success).toBe(false)
  })

  it('取得単価 0 以下を拒否する', () => {
    expect(CreateHoldingSchema.safeParse({ ...validJP, avgCost: -100 }).success).toBe(false)
  })
})
```

### 7-4. API Route 結合テスト

```typescript
// app/api/holdings/route.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { POST } from './route'
import { NextRequest } from 'next/server'

// Supabase をモック
vi.mock('@/lib/supabase/server', () => ({
  createServerClient: vi.fn(() => ({
    auth: {
      getUser: vi.fn().mockResolvedValue({
        data: { user: { id: 'user-1' } },
        error: null,
      }),
    },
    from: vi.fn().mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({ data: { id: 'portfolio-1' }, error: null }),
      insert: vi.fn().mockReturnThis(),
    }),
  })),
}))

function makeRequest(body: object) {
  return new NextRequest('http://localhost/api/holdings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('POST /api/holdings', () => {
  it('正常なリクエストで 201 を返す', async () => {
    const req = makeRequest({
      portfolioId: '550e8400-e29b-41d4-a716-446655440000',
      stockCode: '7203',
      stockName: 'トヨタ自動車',
      market: 'JP',
      quantity: 100,
      avgCost: 2050,
    })
    const res = await POST(req)
    expect(res.status).toBe(201)
  })

  it('バリデーションエラーで 422 を返す', async () => {
    const req = makeRequest({ stockCode: 'INVALID' })
    const res = await POST(req)
    expect(res.status).toBe(422)
  })
})
```

### 7-5. Vitest 設定

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import { resolve } from 'path'

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, '.'),
    },
  },
})
```

### 7-6. package.json スクリプト

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "db:types": "supabase gen types typescript --local > lib/supabase/database.types.ts"
  }
}
```

### 7-7. Zod バリデーションスキーマ（参照）

```typescript
// lib/validations/holding.ts
import { z } from 'zod'

export const CreateHoldingSchema = z.object({
  portfolioId: z.string().uuid('ポートフォリオIDが不正です'),
  stockCode: z.string().regex(
    /^\d{4}$|^[A-Z]{1,5}$/,
    '銘柄コードは4桁数字（日本株）または英字1〜5文字（米国株）で入力してください'
  ),
  stockName: z.string().min(1, '銘柄名を入力してください').max(100),
  market: z.enum(['JP', 'US'], { message: '市場を選択してください' }),
  quantity: z.number({ invalid_type_error: '保有数を入力してください' })
    .positive('保有数は1以上で入力してください'),
  avgCost: z.number({ invalid_type_error: '取得単価を入力してください' })
    .positive('取得単価は0より大きい値を入力してください'),
  acquiredAt: z.string().date().optional(),
  memo: z.string().max(500).optional(),
})

export type CreateHoldingInput = z.infer<typeof CreateHoldingSchema>

export const UpdateHoldingSchema = CreateHoldingSchema
  .omit({ portfolioId: true, stockCode: true, market: true })
  .partial()

export type UpdateHoldingInput = z.infer<typeof UpdateHoldingSchema>
```

---

## セットアップコマンド（Day 1 実行手順）

```bash
# 1. プロジェクト作成
npx create-next-app@latest kabuai \
  --typescript --tailwind --app --src-dir=false \
  --import-alias "@/*"

cd kabuai

# 2. 依存パッケージ
npm install @supabase/ssr @supabase/supabase-js \
  @anthropic-ai/sdk \
  swr zustand \
  zod @hookform/resolvers react-hook-form \
  recharts \
  sonner

# 3. shadcn/ui
npx shadcn@latest init
npx shadcn@latest add button input card table dialog \
  select form label alert badge separator

# 4. 開発ツール
npm install -D vitest @vitest/coverage-v8 \
  @testing-library/react @testing-library/jest-dom \
  jsdom

# 5. Supabase CLI
npm install -D supabase
npx supabase login
npx supabase init
```
