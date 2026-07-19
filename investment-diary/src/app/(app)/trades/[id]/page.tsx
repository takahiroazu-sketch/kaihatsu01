import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getSupabaseServer } from '@/lib/supabase/server'
import type { TradeWithReview } from '@/types/trade'
import type { Review } from '@/types/review'

const EMOTION_LABELS: Record<string, string> = {
  CALM: '冷静',
  GREED: '強欲',
  FEAR: '恐怖',
  FOMO: 'FOMO',
  CONVICTION: '確信',
}

const OUTCOME_LABELS: Record<string, string> = {
  PROFIT: '利益',
  LOSS: '損失',
  EVEN: 'トントン',
}

type PageProps = { params: Promise<{ id: string }> }

export default async function TradeDetailPage({ params }: PageProps) {
  const { id } = await params
  const supabase = await getSupabaseServer()

  const { data } = await supabase
    .from('trades')
    .select('*, reviews(*)')
    .eq('id', id)
    .single()

  if (!data) notFound()

  const reviews = data.reviews as unknown[]
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

  const trade: TradeWithReview = {
    id: String(data.id),
    userId: String(data.user_id),
    stockCode: String(data.stock_code),
    stockName: String(data.stock_name),
    market: String(data.market) as TradeWithReview['market'],
    tradeType: String(data.trade_type) as TradeWithReview['tradeType'],
    quantity: Number(data.quantity),
    price: Number(data.price),
    tradedAt: String(data.traded_at),
    reason: String(data.reason),
    emotionTag: data.emotion_tag != null ? String(data.emotion_tag) as TradeWithReview['emotionTag'] : null,
    createdAt: String(data.created_at),
    updatedAt: String(data.updated_at),
    review,
  }

  const total = trade.quantity * trade.price

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-2 mb-6">
        <Link href="/trades" className="text-sm text-gray-500 hover:text-gray-700">← 一覧に戻る</Link>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-sm font-bold px-3 py-1 rounded-full ${
            trade.tradeType === 'BUY' ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'
          }`}>
            {trade.tradeType === 'BUY' ? '買い' : '売り'}
          </span>
          <span className="text-sm bg-gray-100 text-gray-600 px-3 py-1 rounded-full">{trade.market}</span>
          {trade.emotionTag && (
            <span className="text-sm bg-yellow-50 text-yellow-700 px-3 py-1 rounded-full">
              {EMOTION_LABELS[trade.emotionTag] ?? trade.emotionTag}
            </span>
          )}
        </div>

        <div>
          <h1 className="text-xl font-bold text-gray-900">
            {trade.stockName}
            <span className="text-gray-500 text-base font-normal ml-2">({trade.stockCode})</span>
          </h1>
          <p className="text-sm text-gray-500 mt-1">{trade.tradedAt}</p>
        </div>

        <div className="grid grid-cols-3 gap-4 py-4 border-y border-gray-100">
          <div>
            <p className="text-xs text-gray-500">数量</p>
            <p className="text-sm font-medium mt-1">{trade.quantity.toLocaleString()} 株</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">単価</p>
            <p className="text-sm font-medium mt-1">¥{trade.price.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">合計</p>
            <p className="text-sm font-medium mt-1">¥{total.toLocaleString()}</p>
          </div>
        </div>

        <div>
          <p className="text-xs text-gray-500 mb-1">
            {trade.tradeType === 'BUY' ? '購入理由' : '売却理由'}
          </p>
          <p className="text-sm text-gray-800 whitespace-pre-wrap">{trade.reason}</p>
        </div>
      </div>

      <div className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-gray-900">振り返り</h2>
          {!review && (
            <Link
              href={`/trades/${trade.id}/review`}
              className="text-sm bg-blue-600 text-white px-4 py-1.5 rounded-md hover:bg-blue-700"
            >
              振り返りを記録
            </Link>
          )}
        </div>

        {review ? (
          <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                review.outcome === 'PROFIT' ? 'bg-green-100 text-green-700' :
                review.outcome === 'LOSS' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {OUTCOME_LABELS[review.outcome] ?? review.outcome}
              </span>
              {review.score != null && (
                <span className="text-yellow-400">{'★'.repeat(review.score)}{'☆'.repeat(5 - review.score)}</span>
              )}
            </div>
            {review.goodPoints && (
              <div>
                <p className="text-xs text-gray-500 mb-1">よかった点</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{review.goodPoints}</p>
              </div>
            )}
            {review.improvements && (
              <div>
                <p className="text-xs text-gray-500 mb-1">改善点</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{review.improvements}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-sm text-orange-700">
            まだ振り返りが記録されていません
          </div>
        )}
      </div>
    </div>
  )
}
