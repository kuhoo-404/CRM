import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/threads': 'http://127.0.0.1:8000',
      '/contacts': 'http://127.0.0.1:8000',
      '/dashboard': 'http://127.0.0.1:8000',
      '/rag': 'http://127.0.0.1:8000',
      '/agent': 'http://127.0.0.1:8000',
      '/audit': 'http://127.0.0.1:8000',
      '/respond': 'http://127.0.0.1:8000',
      '/drafts': 'http://127.0.0.1:8000',
    }
  }
})