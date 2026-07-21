<script setup>
import { computed } from 'vue'
import { APPLICATION_STATUS, getApplications } from '../mock/applications.js'
import { EXCHANGE_STATUS, getExchanges } from '../mock/exchanges.js'

const currentUser = { id: 'stu001', name: '张三', studentId: '2024001' }
const completedStatuses = [EXCHANGE_STATUS.COMPLETED, EXCHANGE_STATUS.FINAL_APPROVED]
const pendingStatuses = [EXCHANGE_STATUS.PENDING_CONFIRMATION, EXCHANGE_STATUS.PENDING_FINAL_CONFIRM]
const studentExchanges = computed(() => getExchanges().filter((item) => item.studentId === currentUser.studentId))
const creditedCredits = computed(() => studentExchanges.value.filter((item) => completedStatuses.includes(item.status)).reduce((sum, item) => sum + Number(item.estimatedCredits || 0), 0))
const pendingCount = computed(() => studentExchanges.value.filter((item) => pendingStatuses.includes(item.status)).length)
const availableProjectCount = computed(() => {
  const unavailableIds = new Set(studentExchanges.value.filter((item) => ![EXCHANGE_STATUS.FINAL_REJECTED, EXCHANGE_STATUS.REJECTED].includes(item.status)).map((item) => item.applicationId))
  return getApplications().filter((item) => item.currentUserId === currentUser.id && item.status === APPLICATION_STATUS.FINAL_APPROVED && !unavailableIds.has(item.id)).length
})

const entries = [
  { title: '我的任务', description: '查看和管理分配给你的任务。', to: '/student/tasks' },
  { title: '任务广场', description: '浏览当前可以参与的任务。', to: '/student/task-square' },
  { title: '课时申请', description: '提交新的课时认定申请。', to: '/student/hour-apply' },
  { title: '课时申请进度', description: '查看课时申请的处理状态。', to: '/student/hour-progress' },
  { title: '学分兑换', description: '选择已最终确认的项目申请学分兑换。', to: '/student/credit-exchange' },
  { title: '我的兑换记录', description: '查看兑换进度、处理意见和学分到账结果。', to: '/student/credit-exchange-records' },
  { title: '问题反馈', description: '提交使用过程中遇到的问题。', to: '/student/feedback' },
  { title: '信息通知', description: '查看学生端通知消息。', to: '/student/notifications' },
]
</script>

<template><main class="dashboard-page"><div class="dashboard-content">
  <header class="dashboard-header"><div><p class="eyebrow">STUDENT PORTAL</p><h1>学生端首页</h1><p>欢迎进入课时 / 学分兑换系统学生工作台。</p></div>
    <section class="credit-card" aria-label="我的学分"><div class="credit-card__title"><div><small>MY CREDITS</small><h2>我的学分</h2></div><RouterLink to="/student/credit-exchange-records">查看兑换记录</RouterLink></div><div class="credit-stats"><article><strong>{{ creditedCredits.toFixed(2) }}</strong><span>已到账学分</span></article><article><strong>{{ pendingCount }}</strong><span>待确认兑换申请</span></article><article><strong>{{ availableProjectCount }}</strong><span>可兑换项目</span></article></div></section>
  </header>
  <section class="entry-grid" aria-label="学生端功能入口"><RouterLink v-for="entry in entries" :key="entry.to" :to="entry.to" class="entry-card"><h2>{{ entry.title }}</h2><p>{{ entry.description }}</p></RouterLink></section>
</div></main></template>

<style scoped>
.dashboard-header{display:grid;grid-template-columns:minmax(0,1fr) minmax(420px,520px);align-items:start;gap:28px}.credit-card{padding:20px;border-radius:16px;color:#fff;background:linear-gradient(135deg,#1d4ed8,#4338ca);box-shadow:0 18px 36px rgba(37,99,235,.2)}.credit-card__title{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.credit-card small{opacity:.75;letter-spacing:.12em}.credit-card h2{margin:4px 0}.credit-card a{padding:8px 11px;border:1px solid rgba(255,255,255,.5);border-radius:8px;color:#fff;text-decoration:none;font-weight:700}.credit-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.credit-stats article{padding:12px;border-radius:10px;background:rgba(255,255,255,.12)}.credit-stats strong,.credit-stats span{display:block}.credit-stats strong{font-size:24px}.credit-stats span{margin-top:4px;font-size:12px;opacity:.8}@media(max-width:900px){.dashboard-header{grid-template-columns:1fr}}@media(max-width:520px){.credit-stats{grid-template-columns:1fr}.credit-card__title{flex-direction:column}}
</style>
