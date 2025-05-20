export type App = {
  name: string
  refresh_token_expiry: number
}

export function isAppConnected(app: App) {
  return Date.now() / 1000 < app.refresh_token_expiry
}

export type User = {
  id: string
  email: string
  apps: Record<string, App>
}
