export type Integration = {
  name: string
  active: boolean
}

export type User = {
  id: string
  email: string
  integrations: Record<string, Integration>
}

export type TelegramUser = {
  id: string
  first_name: string
  last_name: string
  username: string
  photo_url: string
  auth_date: number
  hash: string
}
