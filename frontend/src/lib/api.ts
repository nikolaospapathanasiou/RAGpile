import { LoremIpsum } from 'lorem-ipsum'

import { User } from '@/models'

const lorem = new LoremIpsum({
  sentencesPerParagraph: {
    max: 8,
    min: 4,
  },
  wordsPerSentence: {
    max: 16,
    min: 4,
  },
})

type Conversation = {
  id: string
  summary: string
}

export type Message = {
  conversationID: string
  id: string
  text: string
  createdAt: Date
  incoming: boolean
}

const conversations = [
  { id: '1', summary: 'A question about my dog...' },
  { id: '2', summary: 'How to cook napolitana...' },
  {
    id: '3',
    summary: 'I need help with my homework...',
  },
]

const messages: Message[] = []

function generateRandomMessage(): Message {
  const createdAt = new Date()
  createdAt.setTime(createdAt.getTime() - Math.floor(Math.random() * 86400000))
  return {
    conversationID:
      conversations[Math.floor(Math.random() * conversations.length)].id,
    id: Math.random().toString(36).substring(2, 9),
    text: lorem.generateSentences(4),
    incoming: Math.random() > 0.5,
    createdAt: createdAt,
  }
}

for (let i = 0; i < 100; i++) {
  messages.push(generateRandomMessage())
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function getConversations(): Promise<Conversation[]> {
  await sleep(1000)
  return conversations
}

export async function getMessages(conversationID: string): Promise<Message[]> {
  await sleep(1000)
  return messages.filter((m) => m.conversationID === conversationID)
}

function validateResponse(res: Response): Response {
  if (!res.ok) {
    throw new Error(res.statusText)
  }
  return res
}

export async function* sendMessage(content: string): AsyncGenerator<string> {
  const res = await fetch(`/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content }],
      stream: true,
    }),
  })
  validateResponse(res)
  if (!res.body) {
    return
  }

  const reader = res.body.getReader()
  while (true) {
    const { value, done } = await reader.read()
    if (done) {
      break
    }
    const text = new TextDecoder().decode(value)
    const data = JSON.parse(text.substring(text.indexOf('{')))
    if (data.finish_reason) {
      break
    }
    yield data.content
  }
}

export async function loginWithGoogle(): Promise<string> {
  const res = await fetch(`/api/auth/google_login`, {
    method: 'GET',
  })
  return (await validateResponse(res).json()).auth_url
}

export async function authenticateWithGoogle(code: string): Promise<User> {
  const res = await fetch(`/api/auth/google_callback?code=${code}`)
  return await validateResponse(res).json()
}

export async function me(): Promise<User> {
  const res = await fetch('api/auth/me', { method: 'GET' })
  return await validateResponse(res).json()
}

export async function logout(): Promise<void> {
  const res = await fetch('api/auth/logout', { method: 'POST' })
  validateResponse(res)
}
