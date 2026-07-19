import { getAuthUser, apiSuccess, apiError } from '@/lib/api/handler'
import { getSupabaseServer } from '@/lib/supabase/server'
import { UpdateTradeSchema } from '@/lib/validations/trade'
import type { Trade } from '@/types/trade'
import type { Review } from '@/types/review'

type RouteContext = { params: Promise<{ id: string }> }

export async function GET(_request: Request, { params }: RouteContext): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const { id } = await params
  const supabase = await getSupabaseServer()

  const { data, error } = await supabase
    .from('trades')
    .select('*, reviews(*)')
    .eq('id', id)
    .single()

  if (error || !data) return apiError('Trade not found', 'NOT_FOUND', 404)
  if (data['user_id'] !== user.id) return apiError('Forbidden', 'FORBIDDEN', 403)

  return apiSuccess({ trade: mapToTradeWithReview(data) })
}

export async function PATCH(request: Request, { params }: RouteContext): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const { id } = await params
  const body: unknown = await request.json()
  const parsed = UpdateTradeSchema.safeParse(body)
  if (!parsed.success) {
    return apiError(parsed.error.message, 'VALIDATION_ERROR', 422)
  }

  const supabase = await getSupabaseServer()

  const { data: existing } = await supabase
    .from('trades')
    .select('user_id')
    .eq('id', id)
    .single()

  if (!existing) return apiError('Trade not found', 'NOT_FOUND', 404)
  if (existing['user_id'] !== user.id) return apiError('Forbidden', 'FORBIDDEN', 403)

  const updateFields: Record<string, unknown> = {}
  if (parsed.data.stockCode !== undefined) updateFields['stock_code'] = parsed.data.stockCode
  if (parsed.data.stockName !== undefined) updateFields['stock_name'] = parsed.data.stockName
  if (parsed.data.market !== undefined) updateFields['market'] = parsed.data.market
  if (parsed.data.tradeType !== undefined) updateFields['trade_type'] = parsed.data.tradeType
  if (parsed.data.quantity !== undefined) updateFields['quantity'] = parsed.data.quantity
  if (parsed.data.price !== undefined) updateFields['price'] = parsed.data.price
  if (parsed.data.tradedAt !== undefined) updateFields['traded_at'] = parsed.data.tradedAt
  if (parsed.data.reason !== undefined) updateFields['reason'] = parsed.data.reason
  if (parsed.data.emotionTag !== undefined) updateFields['emotion_tag'] = parsed.data.emotionTag

  const { error } = await supabase.from('trades').update(updateFields).eq('id', id)
  if (error) return apiError(error.message, 'INTERNAL_ERROR', 500)

  return apiSuccess({ id })
}

export async function DELETE(_request: Request, { params }: RouteContext): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const { id } = await params
  const supabase = await getSupabaseServer()

  const { data: existing } = await supabase
    .from('trades')
    .select('user_id')
    .eq('id', id)
    .single()

  if (!existing) return apiError('Trade not found', 'NOT_FOUND', 404)
  if (existing['user_id'] !== user.id) return apiError('Forbidden', 'FORBIDDEN', 403)

  const { error } = await supabase.from('trades').delete().eq('id', id)
  if (error) return apiError(error.message, 'INTERNAL_ERROR', 500)

  return new Response(null, { status: 204 })
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

function mapToReview(row: Record<string, unknown>): Review {
  return {
    id: String(row['id']),
    tradeId: String(row['trade_id']),
    outcome: String(row['outcome']) as Review['outcome'],
    goodPoints: row['good_points'] != null ? String(row['good_points']) : null,
    improvements: row['improvements'] != null ? String(row['improvements']) : null,
    score: row['score'] != null ? Number(row['score']) : null,
    createdAt: String(row['created_at']),
    updatedAt: String(row['updated_at']),
  }
}

function mapToTradeWithReview(row: Record<string, unknown>) {
  const reviews = row['reviews']
  const review = Array.isArray(reviews) && reviews.length > 0 && reviews[0] != null
    ? mapToReview(reviews[0] as Record<string, unknown>)
    : null
  return { ...mapToTrade(row), review }
}
