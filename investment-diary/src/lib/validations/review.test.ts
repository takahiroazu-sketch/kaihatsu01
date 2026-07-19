import { describe, it, expect } from 'vitest'
import { CreateReviewSchema, UpdateReviewSchema } from './review'

const validReview = {
  outcome: 'PROFIT' as const,
  goodPoints: '損切りラインを守れた',
  improvements: '次回はエントリーをもう少し待つ',
  score: 4,
}

describe('CreateReviewSchema', () => {
  it('有効な振り返りを受け入れる', () => {
    expect(CreateReviewSchema.safeParse(validReview).success).toBe(true)
  })

  it('outcomeのみ必須で他は省略可能', () => {
    const result = CreateReviewSchema.safeParse({ outcome: 'LOSS' })
    expect(result.success).toBe(true)
  })

  it('不正なoutcomeを拒否する', () => {
    const result = CreateReviewSchema.safeParse({ ...validReview, outcome: 'WIN' })
    expect(result.success).toBe(false)
  })

  it('scoreが6以上の場合は無効', () => {
    const result = CreateReviewSchema.safeParse({ ...validReview, score: 6 })
    expect(result.success).toBe(false)
  })

  it('scoreが0の場合は無効', () => {
    const result = CreateReviewSchema.safeParse({ ...validReview, score: 0 })
    expect(result.success).toBe(false)
  })

  it('goodPointsが1001文字以上の場合は無効', () => {
    const result = CreateReviewSchema.safeParse({
      ...validReview,
      goodPoints: 'a'.repeat(1001),
    })
    expect(result.success).toBe(false)
  })
})

describe('UpdateReviewSchema', () => {
  it('部分更新を受け入れる', () => {
    expect(UpdateReviewSchema.safeParse({ score: 3 }).success).toBe(true)
  })

  it('無効なscoreは部分更新でも拒否する', () => {
    expect(UpdateReviewSchema.safeParse({ score: 0 }).success).toBe(false)
  })
})
