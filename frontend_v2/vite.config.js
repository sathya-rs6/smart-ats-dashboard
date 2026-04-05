import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND = 'http://localhost:8000';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth':          { target: BACKEND, changeOrigin: true },
      '/jobs':          { target: BACKEND, changeOrigin: true },
      '/resumes':       { target: BACKEND, changeOrigin: true },
      '/analyses':      { target: BACKEND, changeOrigin: true },
      '/dashboard':     { target: BACKEND, changeOrigin: true },
      '/chat':          { target: BACKEND, changeOrigin: true },
      '/notifications': { target: BACKEND, changeOrigin: true },
      '/analyze':       { target: BACKEND, changeOrigin: true },
      '/ask':           { target: BACKEND, changeOrigin: true },
      '/job-descriptions': { target: BACKEND, changeOrigin: true },
      '/health':        { target: BACKEND, changeOrigin: true },
    },
  },
})
