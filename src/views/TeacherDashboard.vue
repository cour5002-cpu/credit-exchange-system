<script setup>
import { computed } from 'vue'
import { getAdvisorPendingApplications } from '../mock/applications.js'
import { getAdvisorPendingExchanges } from '../mock/exchanges.js'
const currentAdvisorId = 'T001'
const pendingHours = computed(() => getAdvisorPendingApplications().filter((item) => item.mainAdvisor?.id === currentAdvisorId).length)
const pendingExchanges = computed(() => getAdvisorPendingExchanges(currentAdvisorId).length)
const entries = computed(() => [
  { title: '我的任务', description: '查看和管理指导任务。', to: '/teacher/tasks' },
  { title: '发布任务', description: '创建并发布新的任务。', to: '/teacher/publish-task' },
  { title: '待确认事项', description: `课时申请 ${pendingHours.value} 项，学分兑换 ${pendingExchanges.value} 项。`, to: '/teacher/confirm' },
  { title: '我的处理记录', description: '查看已经处理的业务记录。', to: '/teacher/records' },
  { title: '信息通知', description: '查看指导老师端通知消息。', to: '/teacher/notifications' },
])
</script>

<template>
  <main class="dashboard-page">
    <div class="dashboard-content">
      <header class="dashboard-header">
        <p class="eyebrow">ADVISOR PORTAL</p>
        <h1>指导老师端首页</h1>
        <p>欢迎进入课时 / 学分兑换系统指导老师工作台。</p>
      </header>

      <section class="entry-grid" aria-label="指导老师端功能入口">
        <RouterLink v-for="entry in entries" :key="entry.to" :to="entry.to" class="entry-card">
          <h2>{{ entry.title }}</h2>
          <p>{{ entry.description }}</p>
        </RouterLink>
      </section>
    </div>
  </main>
</template>
