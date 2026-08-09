<script setup>
import { computed, onMounted, ref } from 'vue'
import { getAdminDashboard } from '../api/dashboardApi.js'
import { adaptAdminDashboard } from '../adapters/dashboardAdapter.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const dashboard = ref(null)
const loading = ref(true)
const errorMessage = ref('')

const todoTypes = [
  { type: 'task_publish_review', label: '任务发布确认', to: '/admin/tasks/publish-confirm', detail: (id) => `/admin/tasks/publish-confirm/${id}` },
  { type: 'hour_review_assignment', label: '课时审核分配', to: '/admin/review-assign', detail: (id) => `/admin/review-assign/${id}` },
  { type: 'hour_final_confirmation', label: '课时最终确认', to: '/admin/final-confirm', detail: (id) => `/admin/final-confirm/${id}` },
  { type: 'credit_final_confirmation', label: '学分兑换最终确认', to: '/admin/final-confirm/exchanges', detail: (id) => `/admin/final-confirm/exchanges/${id}` },
  { type: 'appeal_initial_review', label: '申诉初审', to: '/admin/appeals-complaints', detail: (id) => `/admin/appeals-complaints/${id}` },
  { type: 'appeal_review_assignment', label: '申诉复审核分配', to: '/admin/appeals-complaints/assign', detail: (id) => `/admin/appeals-complaints/assign/${id}` },
  { type: 'appeal_final_confirmation', label: '申诉复审最终确认', to: '/admin/final-confirm/appeals', detail: (id) => `/admin/final-confirm/appeals/${id}` },
  { type: 'special_extension_review', label: '特殊延期审核', to: '/admin/extensions', detail: (id) => `/admin/extensions/${id}` },
  { type: 'complaint_unviewed', label: '未查看投诉', to: '/admin/appeals-complaints/complaints', detail: (id) => `/admin/appeals-complaints/complaints/${id}` },
]

const sectionMap = computed(() => new Map((dashboard.value?.sections ?? []).map((section) => [section.todoType, section])))
const todoCards = computed(() => todoTypes.map((definition) => ({
  ...definition,
  count: sectionMap.value.get(definition.type)?.count ?? dashboard.value?.counts?.[definition.type] ?? 0,
})))
const todoItems = computed(() => todoTypes.flatMap((definition) => {
  const section = sectionMap.value.get(definition.type)
  return (section?.items ?? []).map((item) => ({ ...item, ...definition }))
}))

function getDetailPath(item) {
  if (item.bizId === undefined || item.bizId === null || item.bizId === '') return null
  return item.detail(encodeURIComponent(String(item.bizId)))
}

async function loadDashboard() {
  loading.value = true
  errorMessage.value = ''
  try {
    dashboard.value = adaptAdminDashboard(await getAdminDashboard())
  } catch (error) {
    dashboard.value = null
    errorMessage.value = getApiErrorMessage(error, '统计数据加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <main class="page">
    <div class="content">
      <header class="header">
        <div><p class="eyebrow">ADMIN STATISTICS</p><h1>数据统计</h1><p>查看管理员待办事项统计与最近待办。</p></div>
        <RouterLink to="/admin/dashboard" class="link">返回首页</RouterLink>
      </header>

      <section v-if="loading" class="card state">数据加载中...</section>
      <section v-else-if="errorMessage" class="card state error" role="alert">{{ errorMessage }}</section>
      <template v-else-if="dashboard">
        <section class="summary card"><span>总待办数量</span><strong>{{ dashboard.totalPending ?? 0 }}</strong></section>
        <section>
          <h2>待办分类</h2>
          <div class="count-grid">
            <RouterLink v-for="card in todoCards" :key="card.type" :to="card.to" class="count-card">
              <span>{{ card.label }}</span><strong>{{ card.count }}</strong>
            </RouterLink>
          </div>
        </section>
        <section class="list-section">
          <h2>待办列表</h2>
          <p v-if="!todoItems.length" class="card state">暂无待办事项。</p>
          <div v-else class="todo-list">
            <article v-for="item in todoItems" :key="`${item.type}-${item.bizId}`" class="card todo-item">
              <div><p class="type">{{ item.label }}</p><h3>{{ item.title || item.bizNo || `待办 #${item.bizId}` }}</h3><p>业务编号：{{ item.bizNo || '--' }} · 提交人：{{ item.submittedBy || '--' }} · 状态：{{ item.status || '--' }}</p><p>提交时间：{{ item.createdAt || '--' }}</p></div>
              <RouterLink v-if="getDetailPath(item)" :to="getDetailPath(item)" class="link">查看详情</RouterLink>
            </article>
          </div>
        </section>
      </template>
      <section v-else class="card state">暂无统计数据。</section>
    </div>
  </main>
</template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1060px);margin:auto}.header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:24px}.header h1{margin:0}.header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb!important;font-size:12px;font-weight:800;letter-spacing:.12em}.card,.count-card{padding:20px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.summary{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}.summary span{font-weight:700}.summary strong{color:#2563eb;font-size:32px}.count-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.count-card{display:flex;align-items:center;justify-content:space-between;color:#0f172a;font-weight:700;text-decoration:none}.count-card strong{color:#2563eb;font-size:24px}.list-section{margin-top:28px}.todo-list{display:grid;gap:14px}.todo-item{display:flex;align-items:center;justify-content:space-between;gap:20px}.todo-item h3{margin:5px 0 9px}.todo-item p{margin:4px 0;color:#64748b}.type{color:#2563eb!important;font-weight:800}.link{display:inline-block;padding:9px 14px;border:1px solid #bfdbfe;border-radius:9px;color:#1d4ed8;background:#fff;font-weight:700;text-decoration:none;white-space:nowrap}.state{text-align:center;color:#64748b}.error{color:#b91c1c}@media(max-width:760px){.page{padding:24px 14px}.count-grid{grid-template-columns:1fr}.header,.todo-item{align-items:flex-start;flex-direction:column}}
</style>
