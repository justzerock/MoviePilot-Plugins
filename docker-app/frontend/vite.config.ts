import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    target: 'esnext',
    minify: false,
    cssCodeSplit: true,
    outDir: '../app/static',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    cors: true,
    proxy: {
      '/api': 'http://localhost:8899',
      '/data': 'http://localhost:8899',
    },
  },
})
