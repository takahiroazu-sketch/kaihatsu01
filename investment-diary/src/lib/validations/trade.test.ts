import { describe, it, expect } from 'vitest'
import { CreateTradeSchema, UpdateTradeSchema } from './trade'

const validJpBuy = {
  stockCode: '7203',
  stockName: 'トヨタ自動車',
  market: 'JP' as const,
  tradeType: 'BUY' as const,
  quantity: 100,
  price: 2500,
  tradedAt: '2026-06-28',
  reason: 'PERが割安で業績が安定している',
}

describe('CreateTradeSchema', () => {
  it('有効な日本株BUY記録を受け入れる', () => {
    expect(CreateTradeSchema.safeParse(validJpBuy).success).toBe(true)
  })

  it('有効な米国株SELL記録を受け入れる', () => {
    const result = CreateTradeSchema.safeParse({
      ...validJpBuy,
      stockCode: 'AAPL',
      stockName: 'Apple Inc.',
      market: 'US',
      tradeType: 'SELL',
      emotionTag: 'CALM',
    })
    expect(result.success).toBe(true)
  })

  it('reasonが空文字の場合は無効', () => {
    const result = CreateTradeSchema.safeParse({ ...validJpBuy, reason: '' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0]?.message).toContain('売買理由')
    }
  })

  it('不正な銘柄コード形式を拒否する', () => {
    const result = CreateTradeSchema.safeParse({ ...validJpBuy, stockCode: 'ABC12' })
    expect(result.success).toBe(false)
  })

  it('quantityが0以下の場合は無効', () => {
    const result = CreateTradeSchema.safeParse({ ...validJpBuy, quantity: 0 })
    expect(result.success).toBe(false)
  })

  it('priceが負数の場合は無効', () => {
    const result = CreateTradeSchema.safeParse({ ...validJpBuy, price: -100 })
    expect(result.success).toBe(false)
  })

  it('不正な日付形式を拒否する', () => {
    const result = CreateTradeSchema.safeParse({ ...validJpBuy, tradedAt: '2026/06/28' })
    expect(result.success).toBe(false)
  })

  it('emotionTagは省略可能', () => {
    const { emotionTag: _, ...withoutTag } = { ...validJpBuy, emotionTag: undefined }
    const result = CreateTradeSchema.safeParse(withoutTag)
    expect(result.success).toBe(true)
  })

  it('有効なemotionTagを受け入れる', () => {
    const result = CreateTradeSchema.safeParse({ ...validJpBuy, emotionTag: 'FOMO' })
    expect(result.success).toBe(true)
  })

  it('不正なmarketを拒否する', () => {
    const result = CreateTradeSchema.safeParse({ ...validJpBuy, market: 'EU' })
    expect(result.success).toBe(false)
  })
})

describe('UpdateTradeSchema', () => {
  it('部分更新を受け入れる', () => {
    expect(UpdateTradeSchema.safeParse({ quantity: 200 }).success).toBe(true)
  })

  it('空オブジェクトも受け入れる（partial）', () => {
    expect(UpdateTradeSchema.safeParse({}).success).toBe(true)
  })

  it('無効な値は部分更新でも拒否する', () => {
    const result = UpdateTradeSchema.safeParse({ quantity: -1 })
    expect(result.success).toBe(false)
  })
})
