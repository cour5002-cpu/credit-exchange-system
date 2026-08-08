import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'https://3ca735c0.r35.cpolar.top',
        changeOrigin: true,
      },
    },
  },
})
