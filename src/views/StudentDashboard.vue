<script setup>
import { computed, onMounted, ref } from 'vue'
import { getAvailableHourAwards, getStudentExchanges } from '../api/exchangeApi.js'
import { adaptExchangeList, adaptHourAwardList } from '../adapters/exchangeAdapter.js'
import { currentUser as authCurrentUser } from '../stores/authStore.js'

const exchanges = ref([])
const availableAwards = ref([])
const currentStudentId = computed(() => Number(authCurrentUser.value?.student?.id))
const completedStatuses = ['final_approved', 'completed']
const pendingStatuses = ['submitted', 'advisor_approved', 'pending_admin_final']

function exchangeCredits(item) {
  const allocation = item.memberDistributions?.find((row) => Number(row.studentDbId) === currentStudentId.value)
  return Number(allocation?.allocatedCredits ?? item.totalCredit ?? item.earnedCredit ?? item.credit ?? item.estimatedCredits ?? 0)
}

const creditedCredits = computed(() => exchanges.value.filter((item) => completedStatuses.includes(item.status)).reduce((sum, item) => sum + exchangeCredits(item), 0))
const pendingCredits = computed(() => exchanges.value.filter((item) => pendingStatuses.includes(item.status)).reduce((sum, item) => sum + exchangeCredits(item), 0))
const availableProjectCount = computed(() => availableAwards.value.length)

onMounted(async () => {
  const [exchangeResult, awardResult] = await Promise.allSettled([
    getStudentExchanges({ page_size: 100 }),
    getAvailableHourAwards({ page_size: 100 }),
  ])
  if (exchangeResult.status === 'fulfilled') exchanges.value = adaptExchangeList(exchangeResult.value)
  else console.error('[student-dashboard] 学分兑换记录加载失败', exchangeResult.reason)
  if (awardResult.status === 'fulfilled') availableAwards.value = adaptHourAwardList(awardResult.value)
  else console.error('[student-dashboard] 可兑换课时加载失败', awardResult.reason)
})

const entries = [
  { title: '我的任务', description: '查看和管理分配给你的任务。', to: '/student/tasks' },
  { title: '任务广场', description: '浏览当前可以参与的任务。', to: '/student/task-square' },
  { title: '课时申请', description: '提交新的课时认定申请。', to: '/student/hour-apply' },
  { title: '课时申请进度', description: '查看课时申请的处理状态。', to: '/student/hour-progress' },
  { title: '学分兑换', description: '选择已最终确认的项目申请学分兑换。', to: '/student/credit-exchange' },
  { title: '申诉与问题投诉', description: '提交使用过程中遇到的问题。', to: '/student/feedback' },
  { title: '信息通知', description: '查看学生端通知消息。', to: '/student/notifications' },
]
</script>

<template><main class="dashboard-page"><div class="dashboard-content">
  <header class="dashboard-header"><div><p class="eyebrow">STUDENT PORTAL</p><h1>学生端首页</h1><p>欢迎进入课时 / 学分兑换系统学生工作台。</p></div>
    <section class="credit-card" aria-label="我的学分"><div class="credit-card__title"><div><small>MY CREDITS</small><h2>我的学分</h2></div><RouterLink to="/student/credit-exchange-records">查看兑换记录</RouterLink></div><div class="credit-stats"><article><strong>{{ creditedCredits.toFixed(2) }}</strong><span>已到账学分</span></article><article><strong>{{ pendingCredits.toFixed(2) }}</strong><span>待到账学分</span></article><article><strong>{{ availableProjectCount }}</strong><span>可兑换项目</span></article></div></section>
  </header>
  <section class="entry-grid" aria-label="学生端功能入口"><RouterLink v-for="entry in entries" :key="entry.to" :to="entry.to" class="entry-card"><h2>{{ entry.title }}</h2><p>{{ entry.description }}</p></RouterLink></section>
</div></main></template>

<style scoped>
.dashboard-header{display:grid;grid-template-columns:minmax(0,1fr) minmax(420px,520px);align-items:start;gap:28px}.credit-card{padding:20px;border-radius:16px;color:#fff;background:linear-gradient(135deg,#1d4ed8,#4338ca);box-shadow:0 18px 36px rgba(37,99,235,.2)}.credit-card__title{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.credit-card small{opacity:.75;letter-spacing:.12em}.credit-card h2{margin:4px 0}.credit-card a{padding:8px 11px;border:1px solid rgba(255,255,255,.5);border-radius:8px;color:#fff;text-decoration:none;font-weight:700}.credit-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.credit-stats article{padding:12px;border-radius:10px;background:rgba(255,255,255,.12)}.credit-stats strong,.credit-stats span{display:block}.credit-stats strong{font-size:24px}.credit-stats span{margin-top:4px;font-size:12px;opacity:.8}@media(max-width:900px){.dashboard-header{grid-template-columns:1fr}}@media(max-width:520px){.credit-stats{grid-template-columns:1fr}.credit-card__title{flex-direction:column}}
</style>
