import { getAuthUser, apiSuccess, apiError } from '@/lib/api/handler'
import { getSupabaseServer } from '@/lib/supabase/server'
import { CreateTradeSchema } from '@/lib/validations/trade'
import type { Trade } from '@/types/trade'

export async function GET(request: Request): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const { searchParams } = new URL(request.url)
  const limit = Math.min(Number(searchParams.get('limit') ?? '50'), 100)
  const offset = Number(searchParams.get('offset') ?? '0')

  const supabase = await getSupabaseServer()
  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .order('traded_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) return apiError(error.message, 'INTERNAL_ERROR', 500)

  const trades: Trade[] = (data ?? []).map(mapToTrade)
  return apiSuccess({ trades })
}

export async function POST(request: Request): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const body: unknown = await request.json()
  const parsed = CreateTradeSchema.safeParse(body)
  if (!parsed.success) {
    return apiError(parsed.error.message, 'VALIDATION_ERROR', 422)
  }

  const supabase = await getSupabaseServer()
  const { data, error } = await supabase
    .from('trades')
    .insert({
      user_id: user.id,
      stock_code: parsed.data.stockCode,
      stock_name: parsed.data.stockName,
      market: parsed.data.market,
      trade_type: parsed.data.tradeType,
      quantity: parsed.data.quantity,
      price: parsed.data.price,
      traded_at: parsed.data.tradedAt,
      reason: parsed.data.reason,
      emotion_tag: parsed.data.emotionTag ?? null,
    })
    .select('id')
    .single()

  if (error) return apiError(error.message, 'INTERNAL_ERROR', 500)

  return apiSuccess({ id: data.id }, 201)
}

function mapToTrade(row: Record<string, unknown>): Trade {
  return {
    id: String(row['id']),
    userId: String(row['user_id']),
    stockCode: String(row['stock_code']),
    stockName: String(row['stock_name']),
    market: String(row['market']) as Trade['market'],
    tradeType: String(row['trade_type']) as Trade['tradeType'],
    quantity: Number(row['quantity']),
    price: Number(row['price']),
    tradedAt: String(row['traded_at']),
    reason: String(row['reason']),
    emotionTag: row['emotion_tag'] != null ? String(row['emotion_tag']) as Trade['emotionTag'] : null,
    createdAt: String(row['created_at']),
    updatedAt: String(row['updated_at']),
  }
}
