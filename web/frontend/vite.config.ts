import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// API runs on :8765 (uvicorn web.backend.main:app); the dev server proxies /api to it.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5180, strictPort: true, proxy: { '/api': 'http://localhost:8765' } },
})
