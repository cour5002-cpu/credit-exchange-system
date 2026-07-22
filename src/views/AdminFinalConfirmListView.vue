<script setup>
import { computed, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { finalApprove, getAdminFinalApplications } from '../mock/applications.js'

const source = ref('')
const result = ref('')
const keyword = ref('')
const selectedIds = ref([])
const refreshKey = ref(0)
const items = computed(() => {
  refreshKey.value
  const search = keyword.value.trim().toLowerCase()
  return getAdminFinalApplications().filter((item) => (!source.value || item.source === source.value) && (!result.value || item.reviewStatus === result.value) && (!search || item.studentName.toLowerCase().includes(search) || item.title.toLowerCase().includes(search)))
})
const allSelected = computed(() => items.value.length > 0 && items.value.every((item) => selectedIds.value.includes(item.id)))
function toggleAll(event) { const ids = items.value.map((item) => item.id); selectedIds.value = event.target.checked ? [...new Set([...selectedIds.value, ...ids])] : selectedIds.value.filter((id) => !ids.includes(id)) }
function batchConfirm() {
  if (!selectedIds.value.length) return window.alert('请先选择要确认的申请')
  const selected = getAdminFinalApplications().filter((item) => selectedIds.value.includes(item.id))
  if (!selected.length || !window.confirm(`确定批量最终确认通过已选择的 ${selected.length} 条申请吗？`)) return
  selected.forEach((item) => finalApprove(item.id, '管理员批量最终确认通过'))
  selectedIds.value = []
  refreshKey.value += 1
  window.alert('批量最终确认通过成功')
}
</script>

<template><main class="final-page"><div class="page-content">
  <header class="page-header"><div><p class="eyebrow">FINAL CONFIRMATION</p><h1>最终确认</h1><p>处理课时认定与学分兑换最终确认业务。</p></div><RouterLink class="back-link" to="/admin/dashboard">返回管理首页</RouterLink></header>
  <nav class="type-tabs" aria-label="最终确认类型"><RouterLink class="active" to="/admin/final-confirm">课时最终确认</RouterLink><RouterLink to="/admin/final-confirm/exchanges">学分兑换最终确认</RouterLink><RouterLink to="/admin/final-confirm/appeals">申诉复审最终确认</RouterLink></nav>
  <section class="filters"><label><span>申请来源</span><select v-model="source"><option value="">全部来源</option><option value="self">学生自主申请</option><option value="task">任务成果申请</option></select></label><label><span>审核结果</span><select v-model="result"><option value="">全部结果</option><option value="approved">审核通过</option><option value="modified_approved">修改课时后审核通过</option></select></label><label><span>搜索</span><input v-model="keyword" type="search" placeholder="搜索学生姓名或申请标题" /></label></section>
  <section class="list-panel"><div class="panel-header"><div><h2>课时最终确认</h2><span>共 {{ items.length }} 项，已选择 {{ selectedIds.length }} 项</span></div><button @click="batchConfirm">批量最终确认通过</button></div><div class="table-wrapper"><table><thead><tr><th><input type="checkbox" :checked="allSelected" :disabled="!items.length" aria-label="全选待最终确认申请" @change="toggleAll" /></th><th>申请标题</th><th>学生姓名</th><th>申请来源</th><th>原申请课时</th><th>审核认定课时</th><th>审核结果</th><th>审核老师</th><th>审核时间</th><th>当前状态</th><th>操作</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><input v-model="selectedIds" type="checkbox" :value="item.id" /></td><td><strong>{{ item.title }}</strong><small>{{ item.id }}</small></td><td>{{ item.studentName }}</td><td>{{ item.sourceText }}</td><td>{{ item.originalHours }}</td><td>{{ item.recognizedHours }}</td><td><StatusTag :status="item.reviewStatus" /></td><td>{{ item.reviewer?.name || '--' }}</td><td>{{ item.reviewTime }}</td><td><StatusTag :status="item.status" /></td><td><RouterLink class="detail-link" :to="`/admin/final-confirm/${item.id}`">查看详情</RouterLink></td></tr><tr v-if="!items.length"><td class="empty" colspan="11">暂无符合条件的待最终确认申请。</td></tr></tbody></table></div></section>
</div></main></template>

<style scoped>
.final-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.page-content{width:min(100%,1280px);margin:auto}.page-header{display:flex;justify-content:space-between;gap:20px;margin-bottom:18px}.page-header h1{margin:0}.page-header p{color:#64748b}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.back-link,.detail-link{color:#2563eb;font-weight:700;text-decoration:none}.back-link{height:max-content;padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.type-tabs{display:flex;gap:8px;margin-bottom:18px;padding:6px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}.type-tabs a{padding:10px 16px;border-radius:8px;color:#475569;text-decoration:none;font-weight:700}.type-tabs .active{color:#1d4ed8;background:#dbeafe}.filters{display:grid;grid-template-columns:220px 220px 1fr;gap:14px;margin-bottom:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;font-weight:700}.filters select,.filters input{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;font:inherit}.list-panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px}.panel-header h2{margin:0}.panel-header span{color:#64748b}.panel-header button{padding:9px 14px;border:0;border-radius:9px;color:#fff;background:#2563eb;font-weight:700;cursor:pointer}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-top:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc;font-size:13px}input[type=checkbox]{width:17px;height:17px;accent-color:#2563eb}td small{display:block;color:#94a3b8}.empty{text-align:center;color:#64748b}@media(max-width:760px){.final-page{padding:24px 14px}.page-header{flex-direction:column}.filters{grid-template-columns:1fr}.panel-header{align-items:stretch;flex-direction:column;gap:12px}}
</style>
