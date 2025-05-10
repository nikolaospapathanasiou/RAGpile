import { User } from '@/models'

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
