export const ERROR_CODES = [
  'UNAUTHORIZED',
  'FORBIDDEN',
  'NOT_FOUND',
  'VALIDATION_ERROR',
  'CONFLICT',
  'INTERNAL_ERROR',
] as const
export type ErrorCode = typeof ERROR_CODES[number]

export type ApiSuccess<T> = { data: T }

export type ApiError = {
  error: string
  code: ErrorCode
}

export type ApiResult<T> = ApiSuccess<T> | ApiError

export function isApiError(result: unknown): result is ApiError {
  return (
    typeof result === 'object' &&
    result !== null &&
    'error' in result &&
    'code' in result
  )
}
