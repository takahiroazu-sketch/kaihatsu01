import { z } from 'zod'
import { MARKETS, TRADE_TYPES, EMOTION_TAGS } from '@/types/trade'

export const CreateTradeSchema = z.object({
  stockCode: z
    .string()
    .min(1, '銘柄コードを入力してください')
    .regex(/^\d{4}$|^[A-Z]{1,5}$/, '銘柄コードの形式が正しくありません（日本株: 4桁数字、米国株: 英字1〜5文字）'),
  stockName: z
    .string()
    .min(1, '銘柄名を入力してください')
    .max(100, '銘柄名は100文字以内で入力してください'),
  market: z.enum(MARKETS, { message: '市場を選択してください' }),
  tradeType: z.enum(TRADE_TYPES, { message: '売買種別を選択してください' }),
  quantity: z
    .number({ message: '数量を入力してください' })
    .positive('数量は0より大きい値を入力してください'),
  price: z
    .number({ message: '単価を入力してください' })
    .positive('単価は0より大きい値を入力してください'),
  tradedAt: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, '日付の形式が正しくありません（YYYY-MM-DD）'),
  reason: z
    .string()
    .min(1, '売買理由を入力してください')
    .max(1000, '売買理由は1000文字以内で入力してください'),
  emotionTag: z.enum(EMOTION_TAGS).optional(),
})

export const UpdateTradeSchema = CreateTradeSchema.partial()

export type CreateTradeSchema = z.infer<typeof CreateTradeSchema>
export type UpdateTradeSchema = z.infer<typeof UpdateTradeSchema>
