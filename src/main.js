import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { initializeSystemTime } from './services/systemTimeService.js'

initializeSystemTime().finally(() => createApp(App).use(router).mount('#app'))
