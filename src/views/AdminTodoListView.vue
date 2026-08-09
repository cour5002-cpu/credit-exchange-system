<script setup>
import { computed, onMounted, ref } from 'vue'
import { getAdminDashboard } from '../api/dashboardApi.js'
import { adaptAdminDashboard } from '../adapters/dashboardAdapter.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const dashboard = ref(null)
const loading = ref(true)
const errorMessage = ref('')
const selectedType = ref('')

const detailRouteMap = Object.freeze({
  task_publish_review: (id) => `/admin/tasks/publish-confirm/${id}`,
  hour_review_assignment: (id) => `/admin/review-assign/${id}`,
  hour_final_confirmation: (id) => `/admin/final-confirm/${id}`,
  credit_final_confirmation: (id) => `/admin/final-confirm/exchanges/${id}`,
  appeal_initial_review: (id) => `/admin/appeals-complaints/${id}`,
  appeal_review_assignment: (id) => `/admin/appeals-complaints/assign/${id}`,
  appeal_final_confirmation: (id) => `/admin/final-confirm/appeals/${id}`,
  special_extension_review: (id) => `/admin/extensions/${id}`,
  complaint_unviewed: (id) => `/admin/appeals-complaints/complaints/${id}`,
})

const sections = computed(() => dashboard.value?.sections ?? [])
const visibleItems = computed(() => sections.value
  .filter((section) => !selectedType.value || section.todoType === selectedType.value)
  .flatMap((section) => section.items.map((item) => ({
    ...item,
    todoType: section.todoType,
    sectionLabel: section.label,
  }))))

function getDetailPath(item) {
  const createPath = detailRouteMap[item.todoType]
  if (!createPath || item.bizId === undefined || item.bizId === null || item.bizId === '') return null
  return createPath(encodeURIComponent(String(item.bizId)))
}

async function loadDashboard() {
  loading.value = true
  errorMessage.value = ''
  try {
    dashboard.value = adaptAdminDashboard(await getAdminDashboard())
  } catch (error) {
    dashboard.value = null
    errorMessage.value = getApiErrorMessage(error, '待办事项加载失败，请稍后重试')
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
        <div>
          <p class="eyebrow">ADMIN TODO</p>
          <h1>待办事项</h1>
          <p>共 {{ dashboard?.totalPending ?? 0 }} 项待办</p>
        </div>
        <RouterLink to="/admin/dashboard" class="back-link">返回首页</RouterLink>
      </header>

      <section class="card filter-card">
        <label for="todo-type">分类筛选</label>
        <select id="todo-type" v-model="selectedType">
          <option value="">全部分类</option>
          <option v-for="section in sections" :key="section.todoType" :value="section.todoType">
            {{ section.label }}（{{ section.count }}）
          </option>
        </select>
      </section>

      <section v-if="loading" class="card state">数据加载中...</section>
      <section v-else-if="errorMessage" class="card state error" role="alert">{{ errorMessage }}</section>
      <section v-else-if="!visibleItems.length" class="card state">当前分类暂无待办事项。</section>
      <section v-else class="todo-list" aria-label="待办列表">
        <article v-for="item in visibleItems" :key="`${item.todoType}-${item.bizId}`" class="card todo-item">
          <div>
            <p class="type">{{ item.sectionLabel }}</p>
            <h2>{{ item.title || item.bizNo || `待办 #${item.bizId}` }}</h2>
            <p>业务编号：{{ item.bizNo || '--' }}</p>
            <p>提交人：{{ item.submittedBy || '--' }}</p>
            <p>状态：{{ item.status || '--' }}</p>
            <p>提交时间：{{ item.createdAt || '--' }}</p>
          </div>
          <RouterLink v-if="getDetailPath(item)" :to="getDetailPath(item)" class="detail-link">查看详情</RouterLink>
        </article>
      </section>
    </div>
  </main>
</template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,980px);margin:auto}.header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:20px}.header h1{margin:0}.header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb!important;font-size:12px;font-weight:800;letter-spacing:.12em}.card{padding:20px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filter-card{display:flex;align-items:center;gap:12px;margin-bottom:18px}.filter-card label{font-weight:700}.filter-card select{min-width:240px;padding:9px 12px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.todo-list{display:grid;gap:14px}.todo-item{display:flex;align-items:center;justify-content:space-between;gap:20px}.todo-item h2{margin:4px 0 10px;font-size:18px}.todo-item p{margin:4px 0;color:#64748b}.type{color:#2563eb!important;font-size:13px;font-weight:800}.back-link,.detail-link{display:inline-block;padding:9px 14px;border:1px solid #bfdbfe;border-radius:9px;color:#1d4ed8;background:#fff;font-weight:700;text-decoration:none}.state{text-align:center;color:#64748b}.error{color:#b91c1c}@media(max-width:650px){.page{padding:24px 14px}.header,.todo-item,.filter-card{align-items:flex-start;flex-direction:column}.filter-card select{box-sizing:border-box;width:100%;min-width:0}}
</style>
