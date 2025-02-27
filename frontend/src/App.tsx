import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarMenuItem,
  SidebarHeader,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { Input } from '@/components/ui/input'
import { useEffect, useState } from 'react'
import { useApi } from './hooks/use-api'
import { getConversations, getMessages } from './lib/api'

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
            <span>RAGpile</span>
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
        <main className="flex flex-1 flex-col">
          <SidebarTrigger />
          <div className="flex-5/6 overflow-y-auto">
            {messages &&
              !messagesLoading &&
              messages.map((message) => (
                <p className={message.incoming ? 'text-left' : 'text-right'}>
                  {message.text}
                </p>
              ))}
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
