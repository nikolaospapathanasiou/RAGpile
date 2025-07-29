import { useContext } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { UserContext } from '@/contexts/auth-context'
import { logout } from '@/lib/api'

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useContext(UserContext)
  if (!user) return null

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="flex items-center justify-between rounded-lg bg-white p-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">RAGpile</h1>
            <p className="text-gray-600">Welcome back, {user.email}</p>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/ragpile">
              <Button variant="outline">Home</Button>
            </Link>
            <Link to="/ragpile/threads">
              <Button variant="outline">View Threads</Button>
            </Link>
            <Button
              variant="outline"
              onClick={() => logout().then(() => setUser(null))}
            >
              Logout
            </Button>
          </div>
        </header>

        <Separator />

        <section>{children}</section>
      </div>
    </div>
  )
}
