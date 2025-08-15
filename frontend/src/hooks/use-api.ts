import { useState } from 'react'

export function useApi<T, E extends (...args: any[]) => Promise<T>>(
  f: E,
  startLoading: boolean = false
): {
  data: T | null
  setData: (data: T | null) => void
  loading: boolean
  fn: E
} {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(startLoading)
  const fn = (async (...args: Parameters<E>) => {
    setLoading(true)
    try {
      const data = await f(...args)
      setData(data)
      return data
    } finally {
      setLoading(false)
    }
  }) as E
  return { data, setData, loading, fn }
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
