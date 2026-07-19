import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getSupabaseServer } from '@/lib/supabase/server'
import { ReviewForm } from '@/components/review/ReviewForm'

type PageProps = { params: Promise<{ id: string }> }

export default async function ReviewPage({ params }: PageProps) {
  const { id } = await params
  const supabase = await getSupabaseServer()

  const { data: trade } = await supabase
    .from('trades')
    .select('id, stock_name, stock_code, trade_type, traded_at')
    .eq('id', id)
    .single()

  if (!trade) notFound()

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-2 mb-6">
        <Link href={`/trades/${id}`} className="text-sm text-gray-500 hover:text-gray-700">
          ← {String(trade.stock_name)} の記録に戻る
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-1">振り返りを記録</h1>
      <p className="text-sm text-gray-500 mb-6">
        {String(trade.stock_name)} ({String(trade.stock_code)}) — {String(trade.traded_at)}
      </p>

      <ReviewForm tradeId={id} />
    </div>
  )
}
