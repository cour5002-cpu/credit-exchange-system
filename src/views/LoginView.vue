<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getHomePath, login } from '../stores/authStore.js'

const route = useRoute()
const router = useRouter()
const form = reactive({ username: '', password: '' })
const submitting = ref(false)
const errorMessage = ref('')

async function submit() {
  if (!form.username.trim() || !form.password) {
    errorMessage.value = '请输入用户名和密码。'
    return
  }
  submitting.value = true
  errorMessage.value = ''
  try {
    const user = await login({ username: form.username.trim(), password: form.password })
    const requestedPath = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    await router.replace(requestedPath || getHomePath(user))
  } catch (error) {
    errorMessage.value = error?.message || '登录失败，请检查账号、密码及后端服务。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel" aria-labelledby="login-title">
      <p class="eyebrow">课时 / 学分兑换系统</p>
      <h1 id="login-title">用户登录</h1>
      <p class="description">使用后端测试账号登录。认证采用 Session Cookie，不使用 Token。</p>
      <form @submit.prevent="submit">
        <label><span>用户名</span><input v-model="form.username" autocomplete="username" placeholder="student1 / teacher1 / teacher2 / admin" /></label>
        <label><span>密码</span><input v-model="form.password" type="password" autocomplete="current-password" placeholder="请输入密码" /></label>
        <p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p>
        <button class="login-button" type="submit" :disabled="submitting">{{ submitting ? '登录中…' : '登录' }}</button>
      </form>
      <details><summary>联调测试账号</summary><p>学生 student1 / student123</p><p>指导老师 teacher1 / teacher123</p><p>审核老师 teacher2 / teacher123</p><p>管理员 admin / admin123</p></details>
    </section>
  </main>
</template>

<style scoped>.login-page{display:grid;min-height:100vh;place-items:center;padding:24px;background:#f3f6fb}.login-panel{width:min(100%,430px);padding:32px;border:1px solid #e2e8f0;border-radius:18px;background:#fff;box-shadow:0 18px 45px #0f172a12}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.description{color:#64748b;line-height:1.7}form{display:grid;gap:18px;margin-top:24px}label span{display:block;margin-bottom:7px;font-weight:700}input{box-sizing:border-box;width:100%;padding:11px 12px;border:1px solid #cbd5e1;border-radius:9px;font:inherit}.login-button{padding:11px;border:0;border-radius:9px;color:#fff;background:#2563eb;font:inherit;font-weight:800}.login-button:disabled{opacity:.6}.error{margin:0;padding:11px;border-radius:8px;color:#b91c1c;background:#fef2f2}details{margin-top:20px;color:#64748b}details p{margin:6px 0}</style>
