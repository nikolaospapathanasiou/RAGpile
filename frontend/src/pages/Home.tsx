import { useContext, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { UserContext } from '@/contexts/auth-context'
import { useApi } from '@/hooks/use-api'
import { getGoogleTokenURL, googleCallback, logout } from '@/lib/api'
import { isAppConnected } from '@/models'

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
  const [searchParams] = useSearchParams()
  const reason = searchParams.get('reason')
  const code = searchParams.get('code')

  const { loading: googleTokenLoading, fn } = useApi(
    () => googleCallback(reason || '', code || ''),
    true
  )
  useEffect(() => {
    if (code && reason) {
      fn().then(setUser)
    }
  }, [code, reason])

  return (
    <div>
      <div>
        Logged in as {user.email}
        <Button
          disabled={reason == 'email' && googleTokenLoading}
          onClick={() => logout().then(() => setUser(null))}
        >
          Logout
        </Button>
      </div>
      <div className="flex">
        <Agent title="Email">
          <div>Agent content</div>
          <Button
            onClick={() =>
              getGoogleTokenURL('email').then(({ auth_url: authURL }) => {
                window.location.href = authURL
              })
            }
          >
            Login with Google
          </Button>
          {user.apps['email'] && isAppConnected(user.apps['email']) ? (
            <div>Connected</div>
          ) : (
            <div>Not connected</div>
          )}
        </Agent>
      </div>
    </div>
  )
}
