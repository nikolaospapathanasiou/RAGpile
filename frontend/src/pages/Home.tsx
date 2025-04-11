import { useContext } from 'react'

import { Button } from '@/components/ui/button'
import { UserContext } from '@/contexts/auth-context'
import { logout } from '@/lib/api'

export default function Home() {
  const { user, setUser } = useContext(UserContext)
  if (!user) return

  return (
    <div>
      Logged in as {user.email}
      <Button onClick={() => logout().then(() => setUser(null))}>Logout</Button>
    </div>
  )
}
