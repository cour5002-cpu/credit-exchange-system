import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://656ecfdb.r6.cpolar.cn',
        changeOrigin: true,
      },
    },
  },
})
