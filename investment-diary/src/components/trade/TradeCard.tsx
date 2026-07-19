import Link from 'next/link'
import type { TradeWithReview } from '@/types/trade'

const EMOTION_LABEL: Record<string, string> = {
  CALM: '冷静',
  GREED: '強欲',
  FEAR: '恐怖',
  FOMO: 'FOMO',
  CONVICTION: '確信',
}

interface TradeCardProps {
  trade: TradeWithReview
}

export function TradeCard({ trade }: TradeCardProps) {
  const total = trade.quantity * trade.price

  return (
    <Link href={`/trades/${trade.id}`} className="block">
      <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                trade.tradeType === 'BUY'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-red-100 text-red-700'
              }`}>
                {trade.tradeType === 'BUY' ? '買い' : '売り'}
              </span>
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {trade.market}
              </span>
              {trade.emotionTag && (
                <span className="text-xs bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded">
                  {EMOTION_LABEL[trade.emotionTag] ?? trade.emotionTag}
                </span>
              )}
              {!trade.review && (
                <span className="text-xs bg-orange-50 text-orange-600 px-2 py-0.5 rounded">
                  振り返り未記入
                </span>
              )}
            </div>
            <p className="mt-1 font-medium text-gray-900 truncate">
              {trade.stockName}
              <span className="text-gray-500 text-sm ml-1">({trade.stockCode})</span>
            </p>
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">{trade.reason}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-sm font-medium text-gray-900">
              {trade.quantity.toLocaleString()}株
            </p>
            <p className="text-sm text-gray-600">
              ¥{trade.price.toLocaleString()} / 株
            </p>
            <p className="text-xs text-gray-500 mt-1">
              計 ¥{total.toLocaleString()}
            </p>
          </div>
        </div>
        <p className="mt-2 text-xs text-gray-400">{trade.tradedAt}</p>
      </div>
    </Link>
  )
}
