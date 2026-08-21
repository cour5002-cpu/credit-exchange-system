import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://7ff95393.r8.vip.cpolar.cn',
        changeOrigin: true,
      },
    },
  },
})
