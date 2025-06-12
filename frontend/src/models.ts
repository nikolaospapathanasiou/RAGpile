export type Integration = {
  name: string
  active: boolean
}

export type User = {
  id: string
  email: string
  integrations: Record<string, Integration>
}
