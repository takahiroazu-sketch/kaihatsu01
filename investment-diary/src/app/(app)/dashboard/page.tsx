import Link from 'next/link'
import { getSupabaseServer } from '@/lib/supabase/server'
import { TradeCard } from '@/components/trade/TradeCard'
import type { TradeWithReview } from '@/types/trade'
import type { Review } from '@/types/review'

export default async function DashboardPage() {
  const supabase = await getSupabaseServer()
  const { data } = await supabase
    .from('trades')
    .select('*, reviews(*)')
    .order('traded_at', { ascending: false })
    .limit(10)

  const trades: TradeWithReview[] = (data ?? []).map((row) => {
    const reviews = row.reviews as unknown[]
    const reviewRow = Array.isArray(reviews) && reviews.length > 0 ? reviews[0] : null
    const review: Review | null = reviewRow != null && typeof reviewRow === 'object'
      ? mapReview(reviewRow as Record<string, unknown>)
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

  const pendingReviewCount = trades.filter((t) => !t.review).length

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
        <Link
          href="/trades/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
        >
          記録を追加
        </Link>
      </div>

      {pendingReviewCount > 0 && (
        <div className="mb-4 bg-orange-50 border border-orange-200 rounded-md px-4 py-3 text-sm text-orange-700">
          振り返り未記入の記録が {pendingReviewCount} 件あります
        </div>
      )}

      <h2 className="text-sm font-medium text-gray-500 mb-3">直近の売買記録</h2>
      {trades.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg font-medium">まだ売買記録がありません</p>
          <p className="text-sm mt-2">「記録を追加」から始めましょう</p>
        </div>
      ) : (
        <div className="space-y-3">
          {trades.map((trade) => (
            <TradeCard key={trade.id} trade={trade} />
          ))}
        </div>
      )}

      {trades.length > 0 && (
        <Link href="/trades" className="block text-center mt-4 text-sm text-blue-600 hover:underline">
          すべての記録を見る →
        </Link>
      )}
    </div>
  )
}

function mapReview(row: Record<string, unknown>): Review {
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
