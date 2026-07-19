export const MARKETS = ['JP', 'US'] as const
export type Market = typeof MARKETS[number]

export const TRADE_TYPES = ['BUY', 'SELL'] as const
export type TradeType = typeof TRADE_TYPES[number]

export const EMOTION_TAGS = ['CALM', 'GREED', 'FEAR', 'FOMO', 'CONVICTION'] as const
export type EmotionTag = typeof EMOTION_TAGS[number]

export interface Trade {
  id: string
  userId: string
  stockCode: string
  stockName: string
  market: Market
  tradeType: TradeType
  quantity: number
  price: number
  tradedAt: string
  reason: string
  emotionTag: EmotionTag | null
  createdAt: string
  updatedAt: string
}

export type TradeWithReview = Trade & {
  review: Review | null
}

export type CreateTradeInput = {
  stockCode: string
  stockName: string
  market: Market
  tradeType: TradeType
  quantity: number
  price: number
  tradedAt: string
  reason: string
  emotionTag?: EmotionTag
}

export type UpdateTradeInput = Partial<CreateTradeInput>

import type { Review } from './review'
