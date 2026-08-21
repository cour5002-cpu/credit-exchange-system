<script setup>
import { onMounted, ref } from 'vue'
import PaginationControls from '../components/PaginationControls.vue'
import { getAdminComplaints } from '../api/complaintApi.js'
import { adaptComplaintList } from '../adapters/complaintAdapter.js'

const PAGE_SIZE = 20
const status = ref('pending')
const category = ref('')
const keyword = ref('')
const page = ref(1)
const total = ref(0)
const items = ref([])
const loading = ref(false)
const errorMessage = ref('')

function errorText(error) {
  const responseStatus = Number(error?.status ?? error?.response?.status)
  if (responseStatus === 401) return error?.message || '登录已过期，请重新登录。'
  if (responseStatus === 403) return '无权限查看投诉列表。'
  if (responseStatus === 404) return '投诉列表不存在或不可见。'
  return error?.message || '投诉列表加载失败。'
}

function summary(content) {
  const text = String(content || '').replace(/\s+/g, ' ').trim()
  return text.length > 60 ? `${text.slice(0, 60)}…` : text || '--'
}

async function loadComplaints() {
  loading.value = true
  items.value = []
  total.value = 0
  errorMessage.value = ''
  try {
    const payload = await getAdminComplaints({
      status: status.value,
      category: category.value,
      keyword: keyword.value.trim(),
      page: page.value,
      page_size: PAGE_SIZE,
    })
    items.value = adaptComplaintList(payload)
    total.value = Number(payload?.total ?? payload?.pagination?.total ?? items.value.length) || 0
  } catch (error) {
    items.value = []
    total.value = 0
    errorMessage.value = errorText(error)
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  loadComplaints()
}

function changePage(nextPage) {
  page.value = nextPage
  loadComplaints()
}

onMounted(loadComplaints)
</script>

<template><main class="page"><div class="content">
  <header><div><p class="eyebrow">A801 · COMPLAINT MANAGEMENT</p><h1>投诉管理</h1><p>查询并处理学生提交的投诉。</p></div><RouterLink to="/admin/appeals-complaints">返回</RouterLink></header>
  <form class="filters" @submit.prevent="applyFilters"><label><span>状态</span><select v-model="status"><option value="pending">待处理（已提交和处理中）</option><option value="submitted">已提交</option><option value="processing">处理中</option><option value="resolved">已处理</option><option value="all">全部</option></select></label><label><span>分类</span><select v-model="category"><option value="">全部</option><option value="personnel_behavior">人员行为</option><option value="service_quality">服务质量</option><option value="process_violation">流程违规</option><option value="other">其他问题</option></select></label><label class="keyword"><span>搜索</span><input v-model="keyword" type="search" placeholder="投诉编号、内容、姓名或学号" /></label><button type="submit" :disabled="loading">查询</button></form>
  <section class="panel">
    <p v-if="loading" class="state">投诉列表加载中...</p>
    <p v-else-if="errorMessage" class="state error" role="alert">{{ errorMessage }}</p>
    <p v-else-if="!items.length" class="state">暂无投诉记录。</p>
    <div v-else class="table-wrapper"><table><thead><tr><th>投诉编号</th><th>分类</th><th>内容摘要</th><th>提交人</th><th>学号</th><th>状态</th><th>提交时间</th><th>操作</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td>{{ item.complaintNo || '--' }}</td><td>{{ item.categoryText }}</td><td class="summary">{{ summary(item.content) }}</td><td>{{ item.submitter?.name || '--' }}</td><td>{{ item.submitter?.studentNo || '--' }}</td><td>{{ item.statusText }}</td><td>{{ item.submittedAt || item.createdAt || '--' }}</td><td><RouterLink :to="`/admin/appeals-complaints/complaints/${item.id}`">查看详情</RouterLink></td></tr></tbody></table></div>
    <PaginationControls v-if="!errorMessage" :page="page" :page-size="PAGE_SIZE" :total="total" :loading="loading" @change="changePage" />
  </section>
</div></main></template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1280px);margin:auto}header,.filters{display:flex;align-items:center;justify-content:space-between;gap:16px}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.filters,.panel{margin-top:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters label{display:grid;gap:6px}.filters .keyword{flex:1}.filters select,.filters input,.filters button{box-sizing:border-box;width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#fff}.filters button{width:auto;align-self:flex-end;color:#fff;background:#2563eb;font-weight:700}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:13px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}.summary{min-width:220px;white-space:normal;overflow-wrap:anywhere}a{color:#2563eb;font-weight:700;text-decoration:none}.state{padding:30px;text-align:center;color:#64748b}.error{color:#b91c1c}@media(max-width:760px){header,.filters{align-items:stretch;flex-direction:column}.filters button{width:100%}}</style>
