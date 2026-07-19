# DB設計 — KabuAI（Supabase / PostgreSQL）

---

## ER図

```
auth.users (Supabase 管理)
    │
    ├── portfolios (1:N)
    │       │
    │       └── holdings (1:N)
    │
    └── chat_sessions (1:N)
            │
            └── chat_messages (1:N)
```

---

## テーブル定義

### `portfolios` — ポートフォリオ

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| `id` | `uuid` | PK, default gen_random_uuid() | |
| `user_id` | `uuid` | FK → auth.users.id, NOT NULL | |
| `name` | `text` | NOT NULL, default 'メインポートフォリオ' | 例: NISA口座 |
| `description` | `text` | | 任意メモ |
| `created_at` | `timestamptz` | default now() | |
| `updated_at` | `timestamptz` | default now() | |

```sql
CREATE TABLE portfolios (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name        TEXT        NOT NULL DEFAULT 'メインポートフォリオ',
  description TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
CREATE POLICY "portfolios_user_isolation" ON portfolios
  FOR ALL USING (user_id = auth.uid());

-- インデックス
CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
```

---

### `holdings` — 保有銘柄

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| `id` | `uuid` | PK | |
| `portfolio_id` | `uuid` | FK → portfolios.id, NOT NULL | |
| `stock_code` | `text` | NOT NULL | 日本株: `7203`, 米国株: `AAPL` |
| `stock_name` | `text` | NOT NULL | `トヨタ自動車` / `Apple Inc.` |
| `market` | `text` | NOT NULL, CHECK IN ('JP','US') | 市場区分 |
| `quantity` | `numeric(15,4)` | NOT NULL, CHECK > 0 | 保有株数 |
| `avg_cost` | `numeric(15,4)` | NOT NULL, CHECK > 0 | 取得単価（現地通貨） |
| `acquired_at` | `date` | | 取得日 |
| `memo` | `text` | | ユーザーメモ |
| `created_at` | `timestamptz` | default now() | |
| `updated_at` | `timestamptz` | default now() | |

```sql
CREATE TABLE holdings (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id  UUID        NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  stock_code    TEXT        NOT NULL,
  stock_name    TEXT        NOT NULL,
  market        TEXT        NOT NULL CHECK (market IN ('JP', 'US')),
  quantity      NUMERIC(15,4) NOT NULL CHECK (quantity > 0),
  avg_cost      NUMERIC(15,4) NOT NULL CHECK (avg_cost > 0),
  acquired_at   DATE,
  memo          TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (portfolio_id, stock_code)  -- 同一銘柄は1レコード（平均取得単価方式）
);

-- RLS（portfolios 経由でユーザー分離）
ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "holdings_user_isolation" ON holdings
  FOR ALL USING (
    portfolio_id IN (
      SELECT id FROM portfolios WHERE user_id = auth.uid()
    )
  );

CREATE INDEX idx_holdings_portfolio_id ON holdings(portfolio_id);
CREATE INDEX idx_holdings_stock_code   ON holdings(stock_code);
```

---

### `chat_sessions` — チャットセッション

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| `id` | `uuid` | PK | |
| `user_id` | `uuid` | FK → auth.users.id | |
| `portfolio_id` | `uuid` | FK → portfolios.id, NULLABLE | セッション開始時のポートフォリオ |
| `title` | `text` | | 最初のメッセージから自動生成 |
| `created_at` | `timestamptz` | default now() | |

```sql
CREATE TABLE chat_sessions (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  portfolio_id  UUID        REFERENCES portfolios(id) ON DELETE SET NULL,
  title         TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "chat_sessions_user_isolation" ON chat_sessions
  FOR ALL USING (user_id = auth.uid());
```

---

### `chat_messages` — チャットメッセージ

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| `id` | `uuid` | PK | |
| `session_id` | `uuid` | FK → chat_sessions.id | |
| `role` | `text` | NOT NULL, CHECK IN ('user','assistant') | |
| `content` | `text` | NOT NULL | メッセージ本文 |
| `created_at` | `timestamptz` | default now() | |

```sql
CREATE TABLE chat_messages (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID        NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
  content     TEXT        NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "chat_messages_user_isolation" ON chat_messages
  FOR ALL USING (
    session_id IN (
      SELECT id FROM chat_sessions WHERE user_id = auth.uid()
    )
  );

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
```

---

## データ型・設計方針

### 通貨の扱い
- **日本株:** `avg_cost` は円（JPY）で保存
- **米国株:** `avg_cost` はドル（USD）で保存
- 損益計算時: アプリケーション層で `USD × 為替レート` を実施
- DB には生の現地通貨価格のみ保管（為替はリアルタイム取得）

### 平均取得単価の更新
- 追加購入時: アプリケーション側で加重平均を計算して更新

```typescript
const newAvgCost = 
  (holding.avg_cost * holding.quantity + newPrice * newQuantity) /
  (holding.quantity + newQuantity);
```

### `updated_at` 自動更新（トリガー）

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_portfolios_updated_at
  BEFORE UPDATE ON portfolios
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_holdings_updated_at
  BEFORE UPDATE ON holdings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## Supabase 設定チェックリスト

```
✅ RLS を全テーブルで有効化
✅ auth.users は Supabase Auth が管理（直接操作不要）
✅ service_role キーはサーバーサイドのみ使用
✅ anon キーは RLS で保護されたテーブルにのみ使用
✅ Supabase Vault に API キーを保管（環境変数は .env.local のみ）
```
