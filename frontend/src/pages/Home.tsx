import { Button } from '@/components/ui/button'
import { authenticateWithGoogle, loginWithGoogle } from '@/lib/api'

export default function Home() {
  const code = new URLSearchParams(window.location.search).get('code')

  console.log(window.location)
  if (code) {
    console.log('authenticating...')
    authenticateWithGoogle(code).then((user) => {
      console.log(user)
      window.opener.postMessage(user, window.opener.location.origin)
    })
    return <div>Loading...</div>
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
            if (!popup) return
            popup.close()
            window.removeEventListener('message', listener)
            console.log(event)
          }

          window.addEventListener('message', listener)
        }}
      >
        Login with google
      </Button>
    </div>
  )
}
