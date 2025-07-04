import { useContext, useEffect } from 'react'
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'

import { UserContext, UserProvider } from '@/contexts/auth-context.tsx'
import { useApi } from '@/hooks/use-api.ts'
import { me } from '@/lib/api'
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

  if (!user) {
    window.location.href = '/'
  }

  return (
    <Router>
      <Routes>
        <Route path="/ragpile/" element={<Home />} />
      </Routes>
    </Router>
  )
}

export default App
