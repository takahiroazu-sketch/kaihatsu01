import { getSupabaseServer } from '@/lib/supabase/server'
import type { ErrorCode } from '@/types/api'

export function apiSuccess<T>(data: T, status = 200): Response {
  return Response.json({ data }, { status })
}

export function apiError(message: string, code: ErrorCode, status: number): Response {
  return Response.json({ error: message, code }, { status })
}

export async function getAuthUser() {
  const supabase = await getSupabaseServer()
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error || !user) return null
  return user
}
