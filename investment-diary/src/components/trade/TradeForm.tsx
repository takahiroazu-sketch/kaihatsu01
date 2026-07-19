'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { CreateTradeSchema } from '@/lib/validations/trade'
import { MARKETS, TRADE_TYPES, EMOTION_TAGS } from '@/types/trade'

const EMOTION_LABELS: Record<string, string> = {
  CALM: '冷静',
  GREED: '強欲',
  FEAR: '恐怖',
  FOMO: 'FOMO',
  CONVICTION: '確信',
}

export function TradeForm() {
  const router = useRouter()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CreateTradeSchema>({
    resolver: zodResolver(CreateTradeSchema),
    defaultValues: { market: 'JP', tradeType: 'BUY' },
  })

  const tradeType = watch('tradeType')

  async function onSubmit(data: CreateTradeSchema) {
    setServerError(null)
    const response = await fetch('/api/trades', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const body: { error?: string } = await response.json() as { error?: string }
      setServerError(body.error ?? '登録に失敗しました')
      return
    }

    const result: { data: { id: string } } = await response.json() as { data: { id: string } }
    router.push(`/trades/${result.data.id}`)
    router.refresh()
  }

  return (
    <form onSubmit={(e) => { void handleSubmit(onSubmit)(e) }} className="space-y-5 max-w-xl">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">市場</label>
          <select
            {...register('market')}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            {MARKETS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">売買種別</label>
          <select
            {...register('tradeType')}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            {TRADE_TYPES.map((t) => (
              <option key={t} value={t}>{t === 'BUY' ? '買い' : '売り'}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">銘柄コード</label>
          <input
            {...register('stockCode')}
            placeholder="例: 7203 / AAPL"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          {errors.stockCode && <p className="text-xs text-red-500 mt-1">{errors.stockCode.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">銘柄名</label>
          <input
            {...register('stockName')}
            placeholder="例: トヨタ自動車"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          {errors.stockName && <p className="text-xs text-red-500 mt-1">{errors.stockName.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">数量</label>
          <input
            {...register('quantity', { valueAsNumber: true })}
            type="number"
            min="0.0001"
            step="0.0001"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          {errors.quantity && <p className="text-xs text-red-500 mt-1">{errors.quantity.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">単価</label>
          <input
            {...register('price', { valueAsNumber: true })}
            type="number"
            min="0.0001"
            step="0.0001"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          {errors.price && <p className="text-xs text-red-500 mt-1">{errors.price.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">取引日</label>
          <input
            {...register('tradedAt')}
            type="date"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          {errors.tradedAt && <p className="text-xs text-red-500 mt-1">{errors.tradedAt.message}</p>}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {tradeType === 'BUY' ? '購入理由' : '売却理由'}
        </label>
        <textarea
          {...register('reason')}
          rows={4}
          placeholder={tradeType === 'BUY'
            ? 'なぜこの銘柄を買ったのか記録しましょう'
            : 'なぜこの銘柄を売ったのか記録しましょう'}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm resize-none"
        />
        {errors.reason && <p className="text-xs text-red-500 mt-1">{errors.reason.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          感情タグ <span className="text-gray-400 font-normal">（任意）</span>
        </label>
        <select
          {...register('emotionTag')}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="">選択しない</option>
          {EMOTION_TAGS.map((tag) => (
            <option key={tag} value={tag}>{EMOTION_LABELS[tag] ?? tag}</option>
          ))}
        </select>
      </div>

      {serverError && <p className="text-sm text-red-600">{serverError}</p>}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isSubmitting}
          className="bg-blue-600 text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? '登録中...' : '記録を保存'}
        </button>
        <button
          type="button"
          onClick={() => router.back()}
          className="border border-gray-300 text-gray-700 px-6 py-2 rounded-md text-sm font-medium hover:bg-gray-50"
        >
          キャンセル
        </button>
      </div>
    </form>
  )
}
