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
      type: 'human' | 'ai' | 'tool'
      tool_calls: {
        id: string
        name: string
        args: Map<string, string>
      }[]
    }[]
  }
}

export type ToolContent = {
  type: string
  attributes: Map<string, string>
}

export function parseToolContent(content: string): ToolContent[] {
  if (content.startsWith('[')) {
    content = content.slice(1, -1)
  }
  const type = content.split('(', 2)[0]
  const res = content
    .slice(type.length)
    .split(', ' + type)
    .map((item: string) => {
      const attributes: Map<string, string> = new Map()
      const matches = [...item.matchAll(/([a-z_]+)='([^']*)'/g)]
      const matches2 = [...item.matchAll(/([a-z_]+)="([^"]*)"/g)]
      if (!matches) {
        return {
          type,
          attributes,
        }
      }
      for (const match of matches.concat(matches2)) {
        attributes.set(match[1], match[2])
      }
      return {
        type,
        attributes,
      }
    })
  return res
}
