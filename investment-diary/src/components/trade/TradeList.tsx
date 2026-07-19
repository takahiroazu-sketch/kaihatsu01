import { TradeCard } from './TradeCard'
import type { TradeWithReview } from '@/types/trade'

interface TradeListProps {
  trades: TradeWithReview[]
}

export function TradeList({ trades }: TradeListProps) {
  if (trades.length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p className="text-lg font-medium">売買記録がありません</p>
        <p className="text-sm mt-2">「記録を追加」から最初の売買記録を登録しましょう</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {trades.map((trade) => (
        <TradeCard key={trade.id} trade={trade} />
      ))}
    </div>
  )
}
