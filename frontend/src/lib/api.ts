import { LoremIpsum } from 'lorem-ipsum'

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

type Message = {
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
    text: lorem.generateSentences(1),
    incoming: Math.random() > 0.5,
    createdAt: new Date(),
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
