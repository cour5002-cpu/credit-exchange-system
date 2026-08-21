<script setup>
import { onMounted, ref, watch } from 'vue'
import PaginationControls from '../components/PaginationControls.vue'
import { getStudentComplaints } from '../api/complaintApi.js'
import { adaptComplaintList } from '../adapters/complaintAdapter.js'

const PAGE_SIZE = 20
const selectedStatus = ref('all')
const page = ref(1)
const total = ref(0)
const items = ref([])
const loading = ref(false)
const errorMessage = ref('')

function getErrorMessage(error) {
  const status = Number(error?.status ?? error?.response?.status)
  if (status === 403) return '无权限查看投诉记录。'
  if (status === 404) return '投诉记录接口不存在或不可用。'
  return error?.message || '投诉记录加载失败，请稍后重试。'
}

function getSummary(content) {
  const text = String(content || '').replace(/\s+/g, ' ').trim()
  return text.length > 80 ? `${text.slice(0, 80)}…` : text || '--'
}

async function loadComplaints() {
  loading.value = true
  errorMessage.value = ''
  items.value = []
  total.value = 0
  try {
    const payload = await getStudentComplaints({
      status: selectedStatus.value,
      page: page.value,
      page_size: PAGE_SIZE,
    })
    items.value = adaptComplaintList(payload)
    total.value = Number(payload?.total ?? payload?.pagination?.total ?? items.value.length) || 0
  } catch (error) {
    items.value = []
    total.value = 0
    errorMessage.value = getErrorMessage(error)
  } finally {
    loading.value = false
  }
}

function changePage(nextPage) {
  page.value = nextPage
  loadComplaints()
}

watch(selectedStatus, () => {
  page.value = 1
  loadComplaints()
})
onMounted(loadComplaints)
</script>

<template>
  <main class="page"><div class="content">
    <header><div><p class="eyebrow">STUDENT COMPLAINTS</p><h1>我的投诉记录</h1><p>查看投诉提交及处理进度。</p></div><RouterLink to="/student/feedback">返回问题反馈</RouterLink></header>
    <section class="filters"><label><span>状态</span><select v-model="selectedStatus" :disabled="loading"><option value="all">全部</option><option value="submitted">已提交</option><option value="processing">处理中</option><option value="resolved">已处理</option></select></label><RouterLink class="primary" to="/student/complaints/new">提交投诉</RouterLink></section>
    <section class="panel">
      <p v-if="loading" class="state">投诉记录加载中...</p>
      <p v-else-if="errorMessage" class="state error" role="alert">{{ errorMessage }}</p>
      <p v-else-if="!items.length" class="state">暂无投诉记录。</p>
      <div v-else class="list">
        <article v-for="item in items" :key="item.id" class="complaint">
          <div class="heading"><strong>{{ item.complaintNo || `投诉 #${item.id}` }}</strong><span class="status">{{ item.statusText }}</span></div>
          <p class="meta">{{ item.categoryText }} · {{ item.createdAt || item.submittedAt || '--' }}</p>
          <p class="summary">{{ getSummary(item.content) }}</p>
          <RouterLink :to="`/student/complaints/${item.id}`">查看详情</RouterLink>
        </article>
      </div>
      <PaginationControls v-if="!errorMessage" :page="page" :page-size="PAGE_SIZE" :total="total" :loading="loading" @change="changePage" />
    </section>
  </div></main>
</template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,960px);margin:auto}header,.filters,.heading{display:flex;align-items:center;justify-content:space-between;gap:16px}.eyebrow{margin:0;color:#2563eb;font-size:12px;font-weight:800}.filters,.panel{margin-top:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters label{display:flex;align-items:center;gap:10px}.filters select{padding:9px 12px;border:1px solid #cbd5e1;border-radius:8px;background:#fff}.primary,article a,header a{color:#2563eb;font-weight:700;text-decoration:none}.list{display:grid;gap:14px}.complaint{padding:18px;border:1px solid #e2e8f0;border-radius:12px}.status{padding:5px 10px;border-radius:999px;color:#1d4ed8;background:#dbeafe;font-size:13px;font-weight:700}.meta{color:#64748b}.summary{white-space:pre-wrap;overflow-wrap:anywhere}.state{padding:30px;text-align:center;color:#64748b}.error{color:#b91c1c}@media(max-width:640px){header,.filters{align-items:flex-start;flex-direction:column}}</style>
