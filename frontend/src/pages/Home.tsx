import { useContext } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { UserContext } from '@/contexts/auth-context'
import { logout } from '@/lib/api'

function Agent({
  title,
  children,
}: {
  title: string
  children?: React.ReactNode
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
      <CardFooter>Agent footer</CardFooter>
    </Card>
  )
}

export default function Home() {
  const { user, setUser } = useContext(UserContext)
  if (!user) return

  return (
    <div>
      <div>
        Logged in as {user.email}
        <Button onClick={() => logout().then(() => setUser(null))}>
          Logout
        </Button>
      </div>
      <div className="flex">
        <Agent title="Email">
          <div>Agent content</div>
          <Button onClick={() => {}}>Login with Google</Button>
        </Agent>
      </div>
    </div>
  )
}
