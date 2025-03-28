import { useContext } from 'react'

import { Button } from '@/components/ui/button'
import { UserContext } from '@/contexts/auth-context'
import { authenticateWithGoogle, loginWithGoogle, logout } from '@/lib/api'

export default function Home() {
  const code = new URLSearchParams(window.location.search).get('code')

  if (code) {
    authenticateWithGoogle(code).then((user) => {
      window.opener.postMessage(user, window.opener.location.origin)
    })
    return <div>Loading...</div>
  }

  const { user, setUser } = useContext(UserContext)

  if (user) {
    return (
      <div>
        Logged in as {user.email}
        <Button onClick={() => logout().then(() => setUser(null))}>
          Logout
        </Button>
      </div>
    )
  }

  return (
    <div>
      <Button
        onClick={async () => {
          const authURL = await loginWithGoogle()
          const popup = window.open(
            authURL,
            '',
            'popup=true,width=600,height=600'
          )
          const listener = (event: MessageEvent): void => {
            if (popup) {
              popup.close()
            }
            setUser(event.data)
            window.removeEventListener('message', listener)
          }

          window.addEventListener('message', listener)
        }}
      >
        Login with google
      </Button>
    </div>
  )
}
