import { getAuthUser, apiSuccess, apiError } from '@/lib/api/handler'
import { getSupabaseServer } from '@/lib/supabase/server'
import { CreateReviewSchema, UpdateReviewSchema } from '@/lib/validations/review'
import type { Review } from '@/types/review'

type RouteContext = { params: Promise<{ tradeId: string }> }

async function verifyTradeOwnership(tradeId: string, userId: string) {
  const supabase = await getSupabaseServer()
  const { data } = await supabase
    .from('trades')
    .select('user_id')
    .eq('id', tradeId)
    .single()
  if (!data) return 'NOT_FOUND' as const
  if (data['user_id'] !== userId) return 'FORBIDDEN' as const
  return 'OK' as const
}

export async function GET(_request: Request, { params }: RouteContext): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const { tradeId } = await params
  const ownership = await verifyTradeOwnership(tradeId, user.id)
  if (ownership === 'NOT_FOUND') return apiError('Trade not found', 'NOT_FOUND', 404)
  if (ownership === 'FORBIDDEN') return apiError('Forbidden', 'FORBIDDEN', 403)

  const supabase = await getSupabaseServer()
  const { data, error } = await supabase
    .from('reviews')
    .select('*')
    .eq('trade_id', tradeId)
    .single()

  if (error || !data) return apiError('Review not found', 'NOT_FOUND', 404)

  return apiSuccess({ review: mapToReview(data) })
}

export async function POST(request: Request, { params }: RouteContext): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const { tradeId } = await params
  const ownership = await verifyTradeOwnership(tradeId, user.id)
  if (ownership === 'NOT_FOUND') return apiError('Trade not found', 'NOT_FOUND', 404)
  if (ownership === 'FORBIDDEN') return apiError('Forbidden', 'FORBIDDEN', 403)

  const body: unknown = await request.json()
  const parsed = CreateReviewSchema.safeParse(body)
  if (!parsed.success) {
    return apiError(parsed.error.message, 'VALIDATION_ERROR', 422)
  }

  const supabase = await getSupabaseServer()
  const { data, error } = await supabase
    .from('reviews')
    .insert({
      trade_id: tradeId,
      outcome: parsed.data.outcome,
      good_points: parsed.data.goodPoints ?? null,
      improvements: parsed.data.improvements ?? null,
      score: parsed.data.score ?? null,
    })
    .select('id')
    .single()

  if (error) {
    if (error.code === '23505') return apiError('Review already exists', 'CONFLICT', 409)
    return apiError(error.message, 'INTERNAL_ERROR', 500)
  }

  return apiSuccess({ id: data.id }, 201)
}

export async function PATCH(request: Request, { params }: RouteContext): Promise<Response> {
  const user = await getAuthUser()
  if (!user) return apiError('Unauthorized', 'UNAUTHORIZED', 401)

  const { tradeId } = await params
  const ownership = await verifyTradeOwnership(tradeId, user.id)
  if (ownership === 'NOT_FOUND') return apiError('Trade not found', 'NOT_FOUND', 404)
  if (ownership === 'FORBIDDEN') return apiError('Forbidden', 'FORBIDDEN', 403)

  const body: unknown = await request.json()
  const parsed = UpdateReviewSchema.safeParse(body)
  if (!parsed.success) {
    return apiError(parsed.error.message, 'VALIDATION_ERROR', 422)
  }

  const updateFields: Record<string, unknown> = {}
  if (parsed.data.outcome !== undefined) updateFields['outcome'] = parsed.data.outcome
  if (parsed.data.goodPoints !== undefined) updateFields['good_points'] = parsed.data.goodPoints
  if (parsed.data.improvements !== undefined) updateFields['improvements'] = parsed.data.improvements
  if (parsed.data.score !== undefined) updateFields['score'] = parsed.data.score

  const supabase = await getSupabaseServer()
  const { error } = await supabase
    .from('reviews')
    .update(updateFields)
    .eq('trade_id', tradeId)

  if (error) return apiError(error.message, 'INTERNAL_ERROR', 500)

  return apiSuccess({ tradeId })
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
