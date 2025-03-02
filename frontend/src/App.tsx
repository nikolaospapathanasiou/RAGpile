import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { useApi } from '@/hooks/use-api'
import { Message, getConversations, getMessages } from '@/lib/api'
import { useEffect, useState } from 'react'

function MessageBubble({ message }: { message: Message }) {
  if (!message.incoming) {
    return (
      <div className="px-10">
        <p>{message.text}</p>
      </div>
    )
  }

  return (
    <div className="p-1 px-3 flex flex-row-reverse">
      <Card className="w-md bg-primary-foreground">
        <CardContent>{message.text}</CardContent>
        <CardFooter>
          <span className="flex-1 text-right text-xs">
            {message.createdAt.toLocaleString()}
          </span>
        </CardFooter>
      </Card>
    </div>
  )
}

function App() {
  const [conversationID, setConversationID] = useState<string | null>(null)
  const {
    data: conversations,
    loading: conversationsLoading,
    fn: getConversationsFN,
  } = useApi(getConversations)
  useEffect(() => {
    getConversationsFN()
  }, [])

  const {
    data: messages,
    loading: messagesLoading,
    fn: getMessagesFN,
  } = useApi(() => getMessages(conversationID || ''))

  useEffect(() => {
    if (!conversationID) {
      return
    }
    getMessagesFN()
  }, [conversationID])

  return (
    <>
      <SidebarProvider>
        <Sidebar>
          <SidebarHeader>
            <span>ragpile.ai</span>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  {conversations &&
                    !conversationsLoading &&
                    conversations.map((conversation) => {
                      return (
                        <SidebarMenuItem
                          onClick={() => setConversationID(conversation.id)}
                          className="p-2"
                          key={conversation.id}
                        >
                          <span>{conversation.summary}</span>
                        </SidebarMenuItem>
                      )
                    })}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>
        <main className="flex flex-1 flex-col max-h-screen">
          <SidebarTrigger />
          <div className="flex-5/6 shrink overflow-y-auto">
            {messages &&
              !messagesLoading &&
              messages.map((message) => <MessageBubble message={message} />)}
          </div>
          <div className="p-5 flex-1/6 flex flex-col">
            <Input placeholder="Ask a question..." className="flex-1" />
          </div>
        </main>
      </SidebarProvider>
    </>
  )
}

export default App
