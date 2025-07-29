import { useContext, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { UserContext } from '@/contexts/auth-context'
import { useApi } from '@/hooks/use-api'
import {
  getGoogleTokenURL,
  googleCallback,
  logout,
  telegramCallback,
} from '@/lib/api'
import { TelegramUser } from '@/models'

import { Layout } from './Layout'

function StatusIndicator({ isConnected }: { isConnected: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`h-2 w-2 rounded-full ${
          isConnected ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
      <span
        className={`text-sm ${isConnected ? 'text-green-700' : 'text-red-700'}`}
      >
        {isConnected ? 'Connected' : 'Not connected'}
      </span>
    </div>
  )
}

function Integration({
  title,
  children,
  isConnected,
  isLoading,
}: {
  title: string
  children: React.ReactNode
  isConnected: boolean
  isLoading: boolean
}) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{title}</CardTitle>
          {!isLoading && <StatusIndicator isConnected={isConnected} />}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-8 w-32" />
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  )
}

export default function Home() {
  return (
    <Layout>
      <section>
        <h2 className="mb-6 text-xl font-semibold text-gray-900">
          Integrations
        </h2>
        <div className="grid gap-6 md:grid-cols-2">
          <Email />
          <Telegram />
        </div>
      </section>
    </Layout>
  )
}

function Email() {
  const { user, setUser } = useContext(UserContext)
  if (!user) return null

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
  }, [])

  const isConnected = user.integrations?.['email']?.active ?? false

  return (
    <Integration
      title="📧 Email Integration"
      isConnected={isConnected}
      isLoading={googleTokenLoading}
    >
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Connect your Google account to enable email functionality for your
          personal assistant.
        </p>
        {!isConnected && (
          <Button
            disabled={googleTokenLoading}
            onClick={() =>
              getGoogleTokenURL('email').then(({ auth_url: authURL }) => {
                window.location.href = authURL
              })
            }
            className="w-full"
          >
            {googleTokenLoading ? 'Connecting...' : '🔗 Connect Google Account'}
          </Button>
        )}
        {isConnected && (
          <div className="rounded-md bg-green-50 p-3">
            <p className="text-sm text-green-800">
              ✅ Email integration is active and ready to use.
            </p>
          </div>
        )}
      </div>
    </Integration>
  )
}

function Telegram() {
  const { user, setUser } = useContext(UserContext)

  useEffect(() => {
    ;(window as any).onTelegramAuth = (telegramUser: TelegramUser) => {
      console.log('Telegram login success:', telegramUser)
      telegramCallback(telegramUser).then(setUser)
    }

    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?7'
    script.setAttribute('data-telegram-login', 'stavros_test_bot')
    script.setAttribute('data-size', 'medium')
    script.setAttribute('data-userpic', 'false')
    script.setAttribute('data-request-access', 'write')
    script.setAttribute('data-onauth', 'onTelegramAuth(user)')
    script.async = true

    document.getElementById('telegram-login-container')?.appendChild(script)

    return () => {
      delete (window as any).onTelegramAuth
    }
  }, [setUser])

  const isConnected = user?.integrations?.['telegram']?.active ?? false

  return (
    <Integration
      title="📱 Telegram Bot"
      isConnected={isConnected}
      isLoading={false}
    >
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Connect your Telegram account to interact with your personal assistant
          via messages.
        </p>
        {!isConnected && (
          <div className="space-y-3">
            <div
              id="telegram-login-container"
              className="flex justify-center"
            />
            <p className="text-xs text-gray-500 text-center">
              Click the button above to authenticate with Telegram
            </p>
          </div>
        )}
        {isConnected && (
          <div className="rounded-md bg-green-50 p-3">
            <p className="text-sm text-green-800">
              ✅ Telegram bot is connected.
            </p>
          </div>
        )}
      </div>
    </Integration>
  )
}
