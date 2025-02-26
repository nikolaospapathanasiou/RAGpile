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

const conversations = [
  { id: 1, name: 'A question about my dog...' },
  { id: 2, name: 'How to cook napolitana...' },
  {
    id: 3,
    name: 'I need help with my homework...',
  },
]

function App() {
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
                  {conversations.map((conversation) => {
                    return (
                      <SidebarMenuItem className="p-2" key={conversation.id}>
                        <span>{conversation.name}</span>
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
          <div className="flex-5/6 overflow-y-auto">Chat</div>
          <div className="p-5 flex-1/6 flex flex-col">
            <Input placeholder="Ask a question..." className="flex-1" />
          </div>
        </main>
      </SidebarProvider>
    </>
  )
}

export default App
