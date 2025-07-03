import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react-swc'
import express from 'express'
import path from 'path'
import { dirname } from 'path'
import { fileURLToPath } from 'url'
import { createServer as createViteServer } from 'vite'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

async function startServer() {
  const app = express()

  const vite = await createViteServer({
    root: __dirname, // Ensure correct root
    server: { middlewareMode: 'html', hmr: { port: 24678 } },
    base: '/ragpile/',
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  })

  app.use('/ragpile/', (req, res, next) => {
    req.url = req.url.replace(/^\/path/, '') || '/'
    vite.middlewares.handle(req, res, next)
  })
  const port = 5173
  app.listen(port, () => {
    console.log(`Dev server running at http://0.0.0.0:${port}/ragpile/`)
  })
}

startServer()
