import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://3f1e1c4a.r35.cpolar.top',
        changeOrigin: true,
      },
    },
  },
})
