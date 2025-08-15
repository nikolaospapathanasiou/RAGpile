import { Schedule, TelegramUser, Thread, ThreadItem, User } from '@/models'

function validateResponse(res: Response): Response {
  if (!res.ok) {
    throw new Error(res.statusText)
  }
  return res
}

export async function logout(): Promise<void> {
  const res = await fetch('/ragpile/api/auth/logout', { method: 'POST' })
  validateResponse(res)
}

export async function me(): Promise<User> {
  const res = await fetch('/ragpile/api/auth/me', { method: 'GET' })
  return await validateResponse(res).json()
}

type GoogleAuthResponse = {
  auth_url: string
}

export async function getGoogleTokenURL(
  reason: string
): Promise<GoogleAuthResponse> {
  const res = await fetch('/ragpile/api/google_token/' + reason, {
    method: 'GET',
  })
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
  const res = await fetch('/ragpile/api/telegram_callback', {
    method: 'POST',
    body: JSON.stringify(telegramUser),
    headers: { 'Content-type': 'application/json' },
  })
  return await validateResponse(res).json()
}

export async function getThreads(): Promise<ThreadItem[]> {
  const res = await fetch('/ragpile/api/threads', { method: 'GET' })
  return await validateResponse(res).json()
}

export async function getThread(id: string): Promise<Thread> {
  const res = await fetch('/ragpile/api/threads/' + id, { method: 'GET' })
  return await validateResponse(res).json()
}

export async function getSchedules(): Promise<Schedule[]> {
  const res = await fetch('/ragpile/api/schedules', { method: 'GET' })
  return await validateResponse(res).json()
}

export async function updateSchedule(schedule: Schedule): Promise<Schedule> {
  const res = await fetch(`/ragpile/api/schedules/${schedule.id}`, {
    method: 'PUT',
    body: JSON.stringify(schedule),
    headers: { 'Content-type': 'application/json' },
  })
  return await validateResponse(res).json()
}
