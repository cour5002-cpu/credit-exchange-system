<script setup>
import { computed, onMounted, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { getTaskTypeText } from '../mock/tasks.js'
import { getMyTasks } from '../api/taskApi.js';import { adaptTaskList } from '../adapters/taskAdapter.js';import { getApiErrorMessage } from '../utils/apiFeedback.js'

const keyword = ref('')
const filter = ref('')
const remoteTasks=ref([]);onMounted(async()=>{try{remoteTasks.value=adaptTaskList(await getMyTasks({page_size:100}))}catch(error){window.alert(getApiErrorMessage(error,'我的任务加载失败'))}})

const tasks = computed(() => {
  const unique = remoteTasks.value
  return unique.filter((task) => {
    const apply = applyResult(task)
    const matchesStatus = !filter.value
      || (filter.value === 'applied' && ['applied', 'pending_selection'].includes(apply.applyStatus))
      || (filter.value === 'selected' && apply.selected)
      || (filter.value === 'rejected' && apply.applyStatus === 'not_selected')
      || (filter.value === 'leader' && apply.isLeader)
      || (filter.value === 'in_progress' && task.status === 'task_in_progress')
      || (filter.value === 'finished' && task.status === 'result_approved')
    return matchesStatus && (!keyword.value.trim() || task.title.toLowerCase().includes(keyword.value.trim().toLowerCase()))
  }).sort((a, b) => String(b.submitTime).localeCompare(String(a.submitTime)))
})

function applyResult(task) {
  return { applyStatus: task.myRegistration?.status, selected: task.myRegistration?.status === 'selected', isLeader: task.actions?.can_submit_result === true }
}
function taskResult(task) { return task.resultSubmission }
function canSubmitResult(task) {
  const result = taskResult(task)
  return applyResult(task).isLeader && (!result || result.status === 'advisor_rejected')
}
function resultStatus(task) {
  const status = taskResult(task)?.status
  return {
    submitted: '待指导老师确认成果',
    advisor_rejected: '成果已驳回，可重新提交',
    converted_to_hour_application: '已转入课时认定',
  }[status] || '未提交'
}
</script>

<template>
  <main class="page"><div class="content">
    <header><div><p class="eyebrow">S101 · MY TASKS</p><h1>我的任务</h1><p>查看报名、筛选、团队及成果状态。</p></div><RouterLink class="back" to="/student/dashboard">返回首页</RouterLink></header>
    <section class="filters">
      <label><span>任务名称</span><input v-model="keyword" placeholder="搜索任务名称" /></label>
      <label><span>状态</span><select v-model="filter"><option value="">全部</option><option value="applied">已报名</option><option value="selected">已选中</option><option value="rejected">未选中</option><option value="leader">队长任务</option><option value="in_progress">进行中</option><option value="finished">已完成</option></select></label>
    </section>
    <section class="panel"><div class="panel-head"><h2>相关任务</h2><span>共 {{ tasks.length }} 个</span></div><div class="table-wrap"><table>
      <thead><tr><th>任务名称</th><th>任务类型</th><th>指导老师</th><th>报名状态</th><th>筛选结果</th><th>身份</th><th>任务状态</th><th>成果状态</th><th>操作</th></tr></thead>
      <tbody><tr v-for="task in tasks" :key="task.taskId">
        <td><strong>{{ task.title }}</strong><small>{{ task.taskId }}</small></td><td>{{ getTaskTypeText(task.taskType) }}</td><td>{{ task.advisorName }}</td>
        <td>{{ applyResult(task).applyStatus || '--' }}</td><td><StatusTag :status="applyResult(task).selected ? 'confirmed' : applyResult(task).applyStatus === 'not_selected' ? 'rejected' : 'pending'" :text="applyResult(task).selected ? '已选中 / 已参与' : applyResult(task).applyStatus === 'not_selected' ? '未选中' : '等待筛选'" /></td>
        <td>{{ applyResult(task).isLeader ? '队长' : applyResult(task).selected ? '成员' : '--' }}</td><td><StatusTag :status="task.status" /></td><td><StatusTag :status="taskResult(task)?.status || 'draft'" :text="resultStatus(task)" /></td>
        <td><div class="actions"><RouterLink :to="`/student/tasks/${task.taskId}`">查看详情</RouterLink><RouterLink :to="`/student/tasks/${task.taskId}/result`">报名结果</RouterLink><RouterLink :to="`/student/tasks/${task.taskId}/team`">团队信息</RouterLink><RouterLink v-if="canSubmitResult(task)" :to="`/student/tasks/${task.taskId}/result-submit`">上传成果</RouterLink></div></td>
      </tr><tr v-if="!tasks.length"><td class="empty" colspan="9">暂无相关任务。</td></tr></tbody>
    </table></div></section>
  </div></main>
</template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1450px);margin:auto}header,.panel-head{display:flex;justify-content:space-between;gap:20px}header{margin-bottom:20px}h1{margin:0}header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb!important;font-size:12px;font-weight:800;letter-spacing:.12em}.back,.actions a{color:#2563eb;font-weight:700;text-decoration:none}.back{height:max-content;padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.filters{display:grid;grid-template-columns:1fr 280px;gap:16px;margin-bottom:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;font-weight:700}.filters input,.filters select{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-head{align-items:center;padding:18px 20px}.panel-head h2{margin:0}.panel-head span{color:#64748b}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-top:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc}td small{display:block;margin-top:4px;color:#94a3b8}.actions{display:flex;gap:9px}.empty{padding:34px;text-align:center;color:#64748b}@media(max-width:700px){.page{padding:24px 14px}header{flex-direction:column}.filters{grid-template-columns:1fr}.actions{flex-wrap:wrap}}
</style>
