'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { CreateReviewSchema } from '@/lib/validations/review'
import { OUTCOMES } from '@/types/review'

const OUTCOME_LABELS: Record<string, string> = {
  PROFIT: '利益',
  LOSS: '損失',
  EVEN: 'トントン',
}

interface ReviewFormProps {
  tradeId: string
}

export function ReviewForm({ tradeId }: ReviewFormProps) {
  const router = useRouter()
  const [serverError, setServerError] = useState<string | null>(null)
  const [hoverScore, setHoverScore] = useState(0)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<CreateReviewSchema>({
    resolver: zodResolver(CreateReviewSchema),
    defaultValues: { outcome: 'PROFIT' },
  })

  const currentScore = watch('score') ?? 0

  async function onSubmit(data: CreateReviewSchema) {
    setServerError(null)
    const response = await fetch(`/api/reviews/${tradeId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const body: { error?: string } = await response.json() as { error?: string }
      setServerError(body.error ?? '保存に失敗しました')
      return
    }

    router.push(`/trades/${tradeId}`)
    router.refresh()
  }

  return (
    <form onSubmit={(e) => { void handleSubmit(onSubmit)(e) }} className="space-y-5 max-w-xl">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">結果</label>
        <div className="flex gap-3">
          {OUTCOMES.map((outcome) => {
            const selected = watch('outcome') === outcome
            return (
              <label
                key={outcome}
                className={`flex-1 text-center border rounded-md py-2 text-sm cursor-pointer transition-colors ${
                  selected ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium' : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                }`}
              >
                <input
                  {...register('outcome')}
                  type="radio"
                  value={outcome}
                  className="sr-only"
                />
                {OUTCOME_LABELS[outcome] ?? outcome}
              </label>
            )
          })}
        </div>
        {errors.outcome && <p className="text-xs text-red-500 mt-1">{errors.outcome.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          自己評価スコア <span className="text-gray-400 font-normal">（任意）</span>
        </label>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onMouseEnter={() => setHoverScore(star)}
              onMouseLeave={() => setHoverScore(0)}
              onClick={() => setValue('score', star)}
              className={`text-2xl ${
                star <= (hoverScore || currentScore) ? 'text-yellow-400' : 'text-gray-300'
              }`}
            >
              ★
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          よかった点 <span className="text-gray-400 font-normal">（任意）</span>
        </label>
        <textarea
          {...register('goodPoints')}
          rows={3}
          placeholder="計画通りに動けた、損切りを守れた など"
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm resize-none"
        />
        {errors.goodPoints && <p className="text-xs text-red-500 mt-1">{errors.goodPoints.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          次回の改善点 <span className="text-gray-400 font-normal">（任意）</span>
        </label>
        <textarea
          {...register('improvements')}
          rows={3}
          placeholder="エントリーを焦りすぎた、目標株価を設定すべきだった など"
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm resize-none"
        />
        {errors.improvements && <p className="text-xs text-red-500 mt-1">{errors.improvements.message}</p>}
      </div>

      {serverError && <p className="text-sm text-red-600">{serverError}</p>}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isSubmitting}
          className="bg-blue-600 text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? '保存中...' : '振り返りを保存'}
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
