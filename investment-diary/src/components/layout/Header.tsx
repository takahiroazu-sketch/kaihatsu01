'use client'

import { useRouter } from 'next/navigation'
import { getSupabaseClient } from '@/lib/supabase/client'

export function Header() {
  const router = useRouter()

  async function handleSignOut() {
    const supabase = getSupabaseClient()
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <header className="h-14 border-b border-gray-200 bg-white flex items-center justify-end px-6">
      <button
        onClick={() => { void handleSignOut() }}
        className="text-sm text-gray-600 hover:text-gray-900"
      >
        ログアウト
      </button>
    </header>
  )
}
