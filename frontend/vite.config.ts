import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // 開発時は /api をFastAPI(:8000)へプロキシ
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
