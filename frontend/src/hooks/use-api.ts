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

export function useStreamingApi(
  f: (content: string) => AsyncGenerator<string>
): {
  data: string
  loading: boolean
  fn: (content: string) => Promise<void>
} {
  const [data, setData] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const fn = async (content: string) => {
    setLoading(true)
    try {
      for await (const chunk of f(content)) {
        setData((prev) => prev + chunk)
      }
    } finally {
      setLoading(false)
    }
  }
  return { data, loading, fn }
}
