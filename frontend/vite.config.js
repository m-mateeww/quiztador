import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy API calls to Django so session and CSRF cookies stay same-origin.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
