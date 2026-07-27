<script setup>
import { computed, onMounted, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { getAdvisorPendingExchanges } from '../api/exchangeApi.js'
import { adaptExchangeList } from '../adapters/exchangeAdapter.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const keyword = ref('')
const selectedStatus = ref('submitted')
const remoteItems = ref([])
onMounted(async()=>{try{remoteItems.value=adaptExchangeList(await getAdvisorPendingExchanges({page_size:100}))}catch(error){window.alert(getApiErrorMessage(error,'学分兑换待确认列表加载失败'))}})
const items = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return remoteItems.value.filter((item) => {
    const matchesStatus = !selectedStatus.value || item.status === selectedStatus.value
    const matchesKeyword = !search || [item.exchangeId, item.projectTitle, item.taskName, item.captainName, item.teamName]
      .some((value) => String(value || '').toLowerCase().includes(search))
    return matchesStatus && matchesKeyword
  })
})
const totalHours = (item) => item.memberDistributions?.reduce((sum, member) => sum + Number(member.allocatedHours || 0), 0) || 0
const totalCredits = (item) => item.memberDistributions?.reduce((sum, member) => sum + Number(member.allocatedCredits || 0), 0) || 0
</script>

<template><main class="page"><div class="content">
  <header class="header"><div><p class="eyebrow">T601 · CREDIT EXCHANGE CONFIRMATION</p><h1>学分兑换确认</h1><p>确认当前指导团队提交的学分兑换分配方案。</p></div><RouterLink class="back" to="/teacher/dashboard">返回教师首页</RouterLink></header>
  <nav class="tabs"><RouterLink to="/teacher/confirm">课时申请确认</RouterLink><RouterLink class="active" to="/teacher/confirm/exchanges">学分兑换确认</RouterLink></nav>
  <section class="filters"><label><span>搜索</span><input v-model="keyword" type="search" placeholder="编号、项目、任务、队长或团队" /></label><label><span>状态</span><select v-model="selectedStatus"><option value="">全部状态</option><option value="submitted">待指导老师确认</option></select></label></section>
  <section class="panel"><div class="panel-header"><h2>待确认兑换申请</h2><span>共 {{ items.length }} 条</span></div><div class="table-wrap"><table><thead><tr><th>兑换申请编号</th><th>项目名称 / 任务名称</th><th>队长姓名</th><th>团队名称</th><th>总兑换课时</th><th>总兑换学分</th><th>成员数量</th><th>提交时间</th><th>当前状态</th><th>操作</th></tr></thead><tbody>
    <tr v-for="item in items" :key="item.id"><td><strong>{{ item.exchangeId }}</strong></td><td>{{ item.projectTitle }}<small>{{ item.taskName || '--' }}</small></td><td>{{ item.captainName || item.studentName }}</td><td>{{ item.teamName || '--' }}</td><td>{{ totalHours(item) }}</td><td>{{ totalCredits(item).toFixed(2) }}</td><td>{{ item.memberDistributions?.length || 0 }}</td><td>{{ item.submitTime }}</td><td><StatusTag :status="item.status" /></td><td><RouterLink class="detail" :to="`/teacher/confirm/exchanges/${item.id}`">查看详情</RouterLink></td></tr>
    <tr v-if="!items.length"><td class="empty" colspan="10">暂无待确认的学分兑换申请。</td></tr>
  </tbody></table></div></section>
</div></main></template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1380px);margin:auto}.header{display:flex;justify-content:space-between;gap:20px;margin-bottom:18px}.header h1{margin:0 0 8px}.header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb!important;font-size:12px;font-weight:800;letter-spacing:.12em}.back,.detail{color:#2563eb;font-weight:700;text-decoration:none}.back{height:max-content;padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.tabs{display:flex;gap:8px;margin-bottom:18px;padding:6px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}.tabs a{padding:10px 16px;border-radius:8px;color:#475569;text-decoration:none;font-weight:700}.tabs .active{color:#1d4ed8;background:#dbeafe}.filters{display:grid;grid-template-columns:1fr 280px;gap:16px;margin-bottom:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;font-weight:700}.filters input,.filters select{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px}.panel-header h2{margin:0}.panel-header span{color:#64748b}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-top:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc;font-size:13px}td small{display:block;margin-top:4px;color:#94a3b8}.empty{padding:34px;text-align:center;color:#64748b}@media(max-width:700px){.page{padding:24px 14px}.header{flex-direction:column}.filters{grid-template-columns:1fr}.tabs{flex-wrap:wrap}}
</style>
