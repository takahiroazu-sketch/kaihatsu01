import { z } from 'zod'
import { OUTCOMES } from '@/types/review'

export const CreateReviewSchema = z.object({
  outcome: z.enum(OUTCOMES, { message: '結果を選択してください' }),
  goodPoints: z
    .string()
    .max(1000, 'よかった点は1000文字以内で入力してください')
    .optional(),
  improvements: z
    .string()
    .max(1000, '改善点は1000文字以内で入力してください')
    .optional(),
  score: z
    .number()
    .int()
    .min(1, 'スコアは1以上で入力してください')
    .max(5, 'スコアは5以下で入力してください')
    .optional(),
})

export const UpdateReviewSchema = CreateReviewSchema.partial().refine(
  (data) => Object.keys(data).length > 0,
  { message: '更新するフィールドを1つ以上指定してください' }
)

export type CreateReviewSchema = z.infer<typeof CreateReviewSchema>
export type UpdateReviewSchema = z.infer<typeof UpdateReviewSchema>
