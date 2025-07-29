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

export type ThreadItem = {
  id: string
  user_id: string
  created_at: string
}

export type Thread = {
  id: string
  ts: string
  channel_values: {
    messages: {
      content: string
      type: 'human' | 'ai'
      tool_calls: {
        id: string
        name: string
        args: Map<string, string>
      }[]
    }[]
  }
}
