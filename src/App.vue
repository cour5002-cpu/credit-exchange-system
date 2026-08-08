<script setup>
import { useRouter } from 'vue-router'
import { authState, logout } from './stores/authStore.js'

const router = useRouter()

async function handleLogout() {
  try {
    await logout()
  } catch (error) {
    // 即使后端退出请求失败，也会在 store 中清空本地用户状态。
    console.warn('退出请求失败，本地会话已清空。', error)
  }
  await router.replace('/login')
}
</script>

<template>
  <div v-if="authState.user" class="session-bar">
    <span>{{ authState.user.username }}</span>
    <button type="button" @click="handleLogout">退出登录</button>
  </div>
  <div v-if="authState.restoring && !authState.initialized" class="startup-loading" aria-live="polite">
    <div class="startup-loading__spinner" aria-hidden="true"></div>
    <p>正在初始化...</p>
  </div>
  <RouterView />
</template>

<style scoped>.session-bar{position:fixed;z-index:1000;top:12px;right:16px;display:flex;align-items:center;gap:10px;padding:7px 10px;border:1px solid #e2e8f0;border-radius:10px;background:#ffffffee;box-shadow:0 4px 16px #0f172a12}.session-bar span{color:#475569;font-size:13px}.session-bar button{padding:6px 10px;border:1px solid #cbd5e1;border-radius:7px;color:#334155;background:#fff;font:inherit;font-size:13px;font-weight:700;cursor:pointer}.startup-loading{position:fixed;z-index:1100;right:16px;bottom:16px;display:flex;align-items:center;gap:10px;padding:10px 14px;border:1px solid #bfdbfe;border-radius:10px;color:#475569;background:#fff;box-shadow:0 8px 24px #0f172a1f}.startup-loading p{margin:0;font-weight:700}.startup-loading__spinner{width:18px;height:18px;border:3px solid #bfdbfe;border-top-color:#2563eb;border-radius:50%;animation:startup-spin .8s linear infinite}@keyframes startup-spin{to{transform:rotate(360deg)}}</style>
