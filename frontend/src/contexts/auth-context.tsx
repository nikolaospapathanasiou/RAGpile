import { ReactNode, createContext, useState } from 'react'

import { User } from '@/models'

export const UserContext = createContext<{
  user: User | null
  setUser: (user: User | null) => void
}>({ user: null, setUser: () => {} })

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)

  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  )
}
