<script setup>
import { computed, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { TASK_RESULT_STATUS, getAdvisorPendingTaskResults } from '../mock/taskResults.js'

const advisorId = 'T001'
const keyword = ref('')
const statusFilter = ref(TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM)
const results = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return getAdvisorPendingTaskResults(advisorId).filter((item) => {
    const matchesStatus = !statusFilter.value || item.status === statusFilter.value
    const matchesKeyword = !search || [item.taskTitle, item.leaderName].some((value) => String(value || '').toLowerCase().includes(search))
    return matchesStatus && matchesKeyword
  })
})
</script>

<template><main class="page"><div class="content">
  <header><div><p class="eyebrow">T106 · RESULT CONFIRMATION</p><h1>学生成果确认</h1><p>确认队长提交的任务成果，通过后学生方可发起课时申请。</p></div><RouterLink class="back" to="/teacher/confirm">返回待确认事项</RouterLink></header>
  <nav class="tabs"><RouterLink to="/teacher/confirm">课时申请确认</RouterLink><RouterLink to="/teacher/confirm/exchanges">学分兑换确认</RouterLink><RouterLink class="active" to="/teacher/confirm/results">成果确认</RouterLink></nav>
  <section class="filters"><label><span>搜索</span><input v-model="keyword" type="search" placeholder="任务名称或队长姓名" /></label><label><span>成果状态</span><select v-model="statusFilter"><option value="">全部</option><option :value="TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM">待指导老师确认成果</option></select></label></section>
  <section class="panel"><div class="panel-head"><h2>待确认成果</h2><span>共 {{ results.length }} 项</span></div><div class="table-wrap"><table><thead><tr><th>成果编号</th><th>任务名称</th><th>队长姓名</th><th>团队成员数量</th><th>提交时间</th><th>当前成果状态</th><th>操作</th></tr></thead><tbody>
    <tr v-for="item in results" :key="item.resultId"><td>{{ item.resultId }}</td><td>{{ item.taskTitle }}</td><td>{{ item.leaderName }}</td><td>{{ item.teamMembers?.length || 0 }}</td><td>{{ item.submitTime }}</td><td><StatusTag :status="item.status" /></td><td><RouterLink class="detail" :to="`/teacher/confirm/results/${item.resultId}`">查看详情</RouterLink></td></tr>
    <tr v-if="!results.length"><td colspan="7" class="empty">暂无待确认成果</td></tr>
  </tbody></table></div></section>
</div></main></template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1180px);margin:auto}header,.panel-head{display:flex;justify-content:space-between;gap:20px}header{margin-bottom:20px}h1{margin:0}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800;letter-spacing:.12em}header p,.panel-head span{color:#64748b}.back,.detail{color:#2563eb;font-weight:700;text-decoration:none}.back{height:max-content;padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.tabs{display:flex;gap:8px;margin-bottom:18px;padding:6px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}.tabs a{padding:10px 16px;border-radius:8px;color:#475569;text-decoration:none;font-weight:700}.tabs .active{color:#1d4ed8;background:#dbeafe}.filters{display:grid;grid-template-columns:1fr 300px;gap:16px;margin-bottom:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;font-weight:700}.filters input,.filters select{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-head{align-items:center;padding:18px 20px}.panel-head h2{margin:0}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:13px 14px;border-top:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc}.empty{padding:36px;text-align:center;color:#64748b}@media(max-width:680px){.page{padding:24px 14px}header{flex-direction:column}.filters{grid-template-columns:1fr}.tabs{overflow-x:auto}}
</style>
