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

function Integration({
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
        Logged in as {user && user.email}
        <Button onClick={() => logout().then(() => setUser(null))}>
          Logout
        </Button>
      </div>
      <div className="flex">
        <Email />
        <Telegram />
      </div>
    </div>
  )
}

function Email() {
  const { user, setUser } = useContext(UserContext)
  if (!user) return
  const [searchParams, setSearchParams] = useSearchParams()
  const reason = searchParams.get('reason')
  const code = searchParams.get('code')

  const { loading: googleTokenLoading, fn } = useApi(() =>
    googleCallback(reason || '', code || '')
  )
  useEffect(() => {
    if (code && reason) {
      fn().then((user) => {
        setUser(user)
        setSearchParams({})
      })
    }
  }, [code, reason])

  return (
    <Integration title="Email">
      <div>Agent content</div>
      <Button
        disabled={googleTokenLoading}
        onClick={() =>
          getGoogleTokenURL('email').then(({ auth_url: authURL }) => {
            window.location.href = authURL
          })
        }
      >
        Login with Google
      </Button>
      {user.integrations['email']?.active ? (
        <div>Connected</div>
      ) : (
        <div>Not connected</div>
      )}
    </Integration>
  )
}

type TelegramUser = {
  id: string
  first_name: string
  last_name: string
  username: string
  photo_url: string
  auth_date: number
  hash: string
}

function Telegram() {
  const { user, setUser } = useContext(UserContext)
  useEffect(() => {
    ;(window as any).onTelegramAuth = (telegramUser: TelegramUser) => {
      console.log('Telegram login success:', telegramUser)
    }

    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?7'
    script.setAttribute('data-telegram-login', 'stavros_test_bot')
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-userpic', 'false')
    script.setAttribute('data-request-access', 'write')
    script.setAttribute('data-onauth', 'onTelegramAuth(user)')
    script.async = true

    document.getElementById('telegram-login-container')?.appendChild(script)

    return () => {
      delete (window as any).onTelegramAuth
    }
  })

  if (!user) {
  }

  return (
    <Integration title="Telegram">
      <div id="telegram-login-container" />
      {user?.integrations['telegram']?.active ? (
        <div>Connected</div>
      ) : (
        <div>Not connected</div>
      )}
    </Integration>
  )
}
