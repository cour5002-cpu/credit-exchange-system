<script setup>
import { computed } from 'vue'
import { currentReviewerId, getApplications } from '../mock/applications.js'
import { getAppeals } from '../mock/appeals.js'
import NotificationBadge from '../components/NotificationBadge.vue'

const pendingNormal = computed(() => getApplications().filter((item) => item.status === 'pending_reviewer' && item.reviewerId === currentReviewerId.value).length)
const pendingAppeals = computed(() => getAppeals().filter((item) => item.status === 'pending_re_review' && item.reviewTeacherId === currentReviewerId.value).length)
const recordCount = computed(() => {
  const normal = getApplications().filter((item) => item.reviewerId === currentReviewerId.value && item.reviewStatus && item.reviewStatus !== 'pending').length
  const appeals = getAppeals().filter((item) => item.reviewTeacherId === currentReviewerId.value && ['re_review_approved', 're_review_rejected', 'final_confirmed'].includes(item.status)).length
  return normal + appeals
})

const entries = computed(() => [
  { title: '待审核成果', description: `普通审核 ${pendingNormal.value} 项，申诉复审 ${pendingAppeals.value} 项`, count: pendingNormal.value + pendingAppeals.value, to: '/reviewer/review-tasks' },
  { title: '我的审核记录', description: '查看普通课时申请审核和申诉复审记录。', count: recordCount.value, to: '/reviewer/review-records' },
])
</script>

<template>
  <main class="dashboard-page"><div class="dashboard-content">
    <header class="dashboard-header"><p class="eyebrow">REVIEWER PORTAL</p><h1>审核老师端首页</h1><p>审核课时认定材料，并处理管理员分配的申诉复审任务。</p></header>
    <section class="entry-grid" aria-label="审核老师端功能入口">
      <RouterLink v-for="entry in entries" :key="entry.to" :to="entry.to" class="entry-card"><div class="card-heading"><h2>{{ entry.title }}</h2><strong>{{ entry.count }}</strong></div><p>{{ entry.description }}</p></RouterLink>
      <NotificationBadge to="/reviewer/notifications" description="查看审核老师端通知消息。" />
    </section>
  </div></main>
</template>

<style scoped>
.dashboard-page{min-height:100vh;padding:48px 24px;background:#f3f6fb}.dashboard-content{width:min(100%,1080px);margin:auto}.dashboard-header{margin-bottom:28px}.dashboard-header h1{margin:0 0 10px}.dashboard-header p{color:#64748b}.eyebrow{margin:0 0 8px;color:#2563eb;font-size:12px;font-weight:800}.entry-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.entry-card{padding:24px;border:1px solid #e2e8f0;border-radius:16px;color:#0f172a;background:#fff;text-decoration:none;box-shadow:0 8px 25px rgba(15,23,42,.05)}.card-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}.card-heading h2{margin:0;font-size:20px}.card-heading strong{min-width:36px;padding:6px 10px;border-radius:999px;color:#1d4ed8;background:#dbeafe;text-align:center}.entry-card p{margin:14px 0 0;color:#64748b;line-height:1.6}@media(max-width:760px){.entry-grid{grid-template-columns:1fr}}
</style>
