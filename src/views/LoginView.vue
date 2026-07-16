<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const roles = [
  { role: 'student', label: '学生登录', path: '/student/dashboard' },
  { role: 'advisor', label: '指导老师登录', path: '/teacher/dashboard' },
  { role: 'reviewer', label: '审核老师登录', path: '/reviewer/dashboard' },
  { role: 'admin', label: '管理员登录', path: '/admin/dashboard' },
]

function loginAs({ role, path }) {
  localStorage.setItem('role', role)
  router.push(path)
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel" aria-labelledby="login-title">
      <p class="eyebrow">课时 / 学分兑换系统</p>
      <h1 id="login-title">测试角色登录</h1>
      <p class="description">请选择角色进入对应工作台。本阶段仅用于测试页面入口，不会请求真实登录接口。</p>

      <div class="role-buttons">
        <button
          v-for="item in roles"
          :key="item.role"
          class="role-button"
          type="button"
          @click="loginAs(item)"
        >
          {{ item.label }}
        </button>
      </div>
    </section>
  </main>
</template>
