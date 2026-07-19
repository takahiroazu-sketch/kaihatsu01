-- ============================================================
-- trades: 売買記録
-- ============================================================
CREATE TABLE trades (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stock_code   TEXT        NOT NULL CHECK (stock_code ~ '^\d{4}$|^[A-Z]{1,5}$'),
  stock_name   TEXT        NOT NULL,
  market       TEXT        NOT NULL CHECK (market IN ('JP', 'US')),
  trade_type   TEXT        NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
  quantity     NUMERIC(15,4) NOT NULL CHECK (quantity > 0),
  price        NUMERIC(15,4) NOT NULL CHECK (price > 0),
  traded_at    DATE        NOT NULL,
  reason       TEXT        NOT NULL CHECK (length(reason) > 0),
  emotion_tag  TEXT        CHECK (emotion_tag IN ('CALM', 'GREED', 'FEAR', 'FOMO', 'CONVICTION')),
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

CREATE POLICY "trades_user_isolation" ON trades
  FOR ALL
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE INDEX idx_trades_user_id   ON trades(user_id);
CREATE INDEX idx_trades_traded_at ON trades(traded_at DESC);

-- ============================================================
-- reviews: 振り返り（trades と 1:1）
-- ============================================================
CREATE TABLE reviews (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  trade_id     UUID        NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
  outcome      TEXT        NOT NULL CHECK (outcome IN ('PROFIT', 'LOSS', 'EVEN')),
  good_points  TEXT,
  improvements TEXT,
  score        INTEGER     CHECK (score BETWEEN 1 AND 5),
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (trade_id)
);

ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

CREATE POLICY "reviews_user_isolation" ON reviews
  FOR ALL
  USING (
    trade_id IN (
      SELECT id FROM trades WHERE user_id = auth.uid()
    )
  )
  WITH CHECK (
    trade_id IN (
      SELECT id FROM trades WHERE user_id = auth.uid()
    )
  );

CREATE INDEX idx_reviews_trade_id ON reviews(trade_id);

-- ============================================================
-- updated_at 自動更新トリガー
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_trades_updated_at
  BEFORE UPDATE ON trades
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_reviews_updated_at
  BEFORE UPDATE ON reviews
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
