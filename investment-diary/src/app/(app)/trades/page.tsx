import Link from 'next/link'
import { getSupabaseServer } from '@/lib/supabase/server'
import { TradeList } from '@/components/trade/TradeList'
import type { TradeWithReview } from '@/types/trade'
import type { Review } from '@/types/review'

export default async function TradesPage() {
  const supabase = await getSupabaseServer()
  const { data } = await supabase
    .from('trades')
    .select('*, reviews(*)')
    .order('traded_at', { ascending: false })

  const trades: TradeWithReview[] = (data ?? []).map((row) => {
    const reviews = row.reviews as unknown[]
    const reviewRow = Array.isArray(reviews) && reviews.length > 0 ? reviews[0] : null
    const review: Review | null = reviewRow != null && typeof reviewRow === 'object'
      ? {
          id: String((reviewRow as Record<string, unknown>)['id']),
          tradeId: String((reviewRow as Record<string, unknown>)['trade_id']),
          outcome: String((reviewRow as Record<string, unknown>)['outcome']) as Review['outcome'],
          goodPoints: (reviewRow as Record<string, unknown>)['good_points'] != null ? String((reviewRow as Record<string, unknown>)['good_points']) : null,
          improvements: (reviewRow as Record<string, unknown>)['improvements'] != null ? String((reviewRow as Record<string, unknown>)['improvements']) : null,
          score: (reviewRow as Record<string, unknown>)['score'] != null ? Number((reviewRow as Record<string, unknown>)['score']) : null,
          createdAt: String((reviewRow as Record<string, unknown>)['created_at']),
          updatedAt: String((reviewRow as Record<string, unknown>)['updated_at']),
        }
      : null
    return {
      id: String(row.id),
      userId: String(row.user_id),
      stockCode: String(row.stock_code),
      stockName: String(row.stock_name),
      market: String(row.market) as TradeWithReview['market'],
      tradeType: String(row.trade_type) as TradeWithReview['tradeType'],
      quantity: Number(row.quantity),
      price: Number(row.price),
      tradedAt: String(row.traded_at),
      reason: String(row.reason),
      emotionTag: row.emotion_tag != null ? String(row.emotion_tag) as TradeWithReview['emotionTag'] : null,
      createdAt: String(row.created_at),
      updatedAt: String(row.updated_at),
      review,
    }
  })

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">売買記録</h1>
        <Link
          href="/trades/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
        >
          記録を追加
        </Link>
      </div>
      <TradeList trades={trades} />
    </div>
  )
}
