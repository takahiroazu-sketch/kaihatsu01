import { TradeForm } from '@/components/trade/TradeForm'

export default function NewTradePage() {
  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">売買記録を追加</h1>
      <TradeForm />
    </div>
  )
}
