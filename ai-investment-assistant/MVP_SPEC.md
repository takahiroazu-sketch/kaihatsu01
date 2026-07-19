# MVP仕様書 — KabuAI

**対象期間:** 2週間（Day 1 〜 Day 14）  
**技術スタック:** Next.js 15 / TypeScript / Supabase / Tailwind CSS / Claude API

---

## 1. テックスタック詳細

| 分類 | 技術 | 選定理由 |
|------|------|---------|
| フレームワーク | Next.js 15（App Router） | Server Components で API コスト削減、SEO 対応 |
| 言語 | TypeScript | 型安全、IDE 補完、バグ早期発見 |
| DB / Auth | Supabase | RLS 標準搭載、Auth 組込み、個人開発向け無料枠 |
| スタイリング | Tailwind CSS | 高速 UI 構築、クラス名管理不要 |
| コンポーネント | shadcn/ui | アクセシブル、コピペ型でバンドルサイズ最小 |
| チャート | Recharts | React ネイティブ、軽量 |
| AI | Anthropic Claude API（claude-sonnet-4-6） | 文脈理解・日本語品質最高水準 |
| 株価データ | Yahoo Finance (yfinance-compatible) / J-Quants | 無料、日米両対応 |
| デプロイ | Vercel | Next.js 最適化、CI/CD 自動化 |
| 状態管理 | Zustand + SWR | 軽量、キャッシュ管理容易 |
| バリデーション | Zod | TypeScript ファースト |

---

## 2. MVP スコープ定義

### In Scope（必ず作る）
```
✅ 認証（メール / Google）
✅ ポートフォリオ CRUD（銘柄・保有数・取得単価）
✅ 現在株価取得（日本株・米国株・為替）
✅ 損益ダッシュボード（合計・銘柄別一覧）
✅ AI チャット（Claude API + ポートフォリオ文脈）
✅ レスポンシブ UI
✅ Vercel デプロイ
```

### Out of Scope（v2 以降）
```
❌ 証券会社連携
❌ プッシュ通知
❌ バックテスト
❌ CSV インポート / エクスポート
❌ 課金・プラン機能
❌ ダーク / ライトモード切替（Tailwind でダーク固定か明確にする）
```

---

## 3. ディレクトリ構成

```
kabuai/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (app)/
│   │   ├── layout.tsx          # サイドバー付きレイアウト
│   │   ├── dashboard/page.tsx
│   │   ├── portfolio/
│   │   │   ├── page.tsx        # 一覧
│   │   │   └── [id]/page.tsx   # 詳細 / 編集
│   │   └── chat/page.tsx
│   ├── api/
│   │   ├── portfolio/route.ts
│   │   ├── holdings/route.ts
│   │   ├── prices/route.ts
│   │   └── chat/route.ts
│   └── layout.tsx
├── components/
│   ├── ui/                     # shadcn/ui
│   ├── portfolio/
│   │   ├── HoldingCard.tsx
│   │   ├── AddHoldingModal.tsx
│   │   └── PortfolioSummary.tsx
│   ├── dashboard/
│   │   ├── PnLSummary.tsx
│   │   ├── AllocationChart.tsx
│   │   └── HoldingTable.tsx
│   └── chat/
│       ├── ChatWindow.tsx
│       └── MessageBubble.tsx
├── lib/
│   ├── supabase/
│   │   ├── client.ts           # ブラウザ用
│   │   └── server.ts           # Server Component 用
│   ├── ai/
│   │   ├── claude.ts           # Claude API ラッパー
│   │   └── prompts.ts          # システムプロンプト
│   └── prices/
│       ├── fetcher.ts          # 株価取得統合
│       ├── japan.ts            # 日本株
│       └── us.ts               # 米国株
├── types/
│   ├── portfolio.ts
│   ├── holding.ts
│   └── chat.ts
└── middleware.ts               # 認証ガード
```

---

## 4. コア機能仕様

### 4-1. 株価取得戦略

```typescript
// 優先順位:
// 日本株  → J-Quants API（無料枠）→ フォールバック: Yahoo Finance JP
// 米国株  → Yahoo Finance (yfinance scraping互換) 
// 為替    → ExchangeRate-API（無料）

// キャッシュ戦略: Next.js revalidate = 900（15分）
```

**銘柄コード規則:**
- 日本株: 4桁数字（例: `7203`）→ サフィックス `.T` 付加
- 米国株: アルファベット（例: `AAPL`, `VTI`）

### 4-2. AI チャット プロンプト設計

```typescript
const buildSystemPrompt = (portfolio: Portfolio, holdings: Holding[]) => `
あなたは個人投資家の投資分析をサポートするAIアシスタントです。

【重要なガイドライン】
- 根拠のない銘柄推奨は絶対に行わない
- 分析・推奨は必ず数値的根拠（PER/ROE/配当利回り/騰落率等）を明示する
- 「投資判断はご自身の責任で行ってください」を適宜リマインドする
- 日本語で回答する

【ユーザーの現在のポートフォリオ】
ポートフォリオ名: ${portfolio.name}
総評価額: ${formatCurrency(portfolio.totalValue)}円
評価損益: ${formatPnL(portfolio.totalPnL)}円 (${portfolio.pnlRate}%)

【保有銘柄一覧】
${holdings.map(h => `
- ${h.stockName}（${h.stockCode}）
  保有数: ${h.quantity}株 / 取得単価: ${h.avgCost}円
  現在値: ${h.currentPrice}円 / 評価損益: ${h.pnl}円 (${h.pnlRate}%)
`).join('')}

ユーザーの質問に対して、上記ポートフォリオ情報を踏まえて回答してください。
`;
```

### 4-3. RLS ポリシー設計

```sql
-- 全テーブルに適用: ユーザーは自分のデータのみアクセス可
CREATE POLICY "user_isolation" ON portfolios
  USING (user_id = auth.uid());
```

---

## 5. 環境変数

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Claude API
ANTHROPIC_API_KEY=

# 株価データ
JQUANTS_REFRESH_TOKEN=         # J-Quants（日本株）
EXCHANGE_RATE_API_KEY=         # 為替レート

# App
NEXT_PUBLIC_APP_URL=
```

---

## 6. 法的免責表示（必須）

以下をフッターおよび AI チャット画面に表示:

> 本サービスは投資情報の提供を目的としており、投資助言・勧誘を行うものではありません。  
> 投資判断はご自身の責任において行ってください。
