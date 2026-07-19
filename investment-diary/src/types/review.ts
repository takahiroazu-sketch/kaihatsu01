export const OUTCOMES = ['PROFIT', 'LOSS', 'EVEN'] as const
export type Outcome = typeof OUTCOMES[number]

export interface Review {
  id: string
  tradeId: string
  outcome: Outcome
  goodPoints: string | null
  improvements: string | null
  score: number | null
  createdAt: string
  updatedAt: string
}

export type CreateReviewInput = {
  outcome: Outcome
  goodPoints?: string
  improvements?: string
  score?: number
}

export type UpdateReviewInput = Partial<CreateReviewInput>
