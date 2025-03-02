import { useState } from 'react'

export function useApi<T>(f: () => Promise<T>): {
  data: T | null
  loading: boolean
  fn: () => Promise<T>
} {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const fn = async () => {
    setLoading(true)
    const data = await f()
    setData(data)
    setLoading(false)
    return data
  }
  return { data, loading, fn }
}
