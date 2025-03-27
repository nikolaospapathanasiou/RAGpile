import { useContext, useEffect } from 'react'
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'

import { UserContext, UserProvider } from '@/contexts/auth-context.tsx'
import { useApi } from '@/hooks/use-api.ts'
import { me } from '@/lib/api'
import Chat from '@/pages/Chat.tsx'
import Home from '@/pages/Home.tsx'

function App() {
  return (
    <UserProvider>
      <AppRoutes />
    </UserProvider>
  )
}

function AppRoutes() {
  const { user, setUser } = useContext(UserContext)
  const { loading, fn: getMe } = useApi(me, true)
  useEffect(() => {
    if (!user) {
      getMe()
        .then(setUser)
        .catch(() => {})
    }
  }, [])

  if (loading) {
    return
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        {user && <Route path="/chat" element={<Chat />} />}
      </Routes>
    </Router>
  )
}

export default App
