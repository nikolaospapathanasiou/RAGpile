import { TelegramUser, User } from '@/models'

function validateResponse(res: Response): Response {
  if (!res.ok) {
    throw new Error(res.statusText)
  }
  return res
}

export async function logout(): Promise<void> {
  const res = await fetch('api/auth/logout', { method: 'POST' })
  validateResponse(res)
}

export async function me(): Promise<User> {
  const res = await fetch('api/auth/me', { method: 'GET' })
  return await validateResponse(res).json()
}

type GoogleAuthResponse = {
  auth_url: string
}

export async function getGoogleTokenURL(
  reason: string
): Promise<GoogleAuthResponse> {
  const res = await fetch('api/google_token/' + reason, { method: 'GET' })
  return await validateResponse(res).json()
}

export async function googleCallback(
  reason: string,
  code: string
): Promise<User> {
  const res = await fetch(
    'api/google_token_callback/' + reason + '?code=' + code,
    { method: 'POST' }
  )
  return await validateResponse(res).json()
}

export async function telegramCallback(
  telegramUser: TelegramUser
): Promise<User> {
  const res = await fetch('api/telegram_callback', {
    method: 'POST',
    body: JSON.stringify(telegramUser),
    headers: { 'Content-type': 'application/json' },
  })
  return await validateResponse(res).json()
}
