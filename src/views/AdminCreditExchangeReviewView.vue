<script setup>
import { computed, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import {
  EXCHANGE_STATUS,
  batchFinalApproveExchanges,
  batchFinalRejectExchanges,
  getExchangeFinalConfirmList,
} from '../mock/exchanges.js'

const keyword = ref('')
const selectedIds = ref([])
const batchComment = ref('')
const batchResult = ref(null)
const refreshKey = ref(0)
const items = computed(() => {
  refreshKey.value
  const search = keyword.value.trim().toLowerCase()
  return getExchangeFinalConfirmList().filter((item) => !search || [item.exchangeId, item.studentName, item.studentId, item.teamName, item.taskName].some((value) => String(value || '').toLowerCase().includes(search)))
})
const allSelected = computed(() => items.value.length > 0 && items.value.every((item) => selectedIds.value.includes(item.id)))
const partiallySelected = computed(() => !allSelected.value && items.value.some((item) => selectedIds.value.includes(item.id)))

function toggleAll(event) {
  const ids = items.value.map((item) => item.id)
  selectedIds.value = event.target.checked ? [...new Set([...selectedIds.value, ...ids])] : selectedIds.value.filter((id) => !ids.includes(id))
}

function finishBatch(result, action) {
  batchResult.value = { ...result, action }
  selectedIds.value = []
  refreshKey.value += 1
}

function batchApprove() {
  if (!selectedIds.value.length) return window.alert('请先选择要最终确认兑换的申请。')
  if (!window.confirm(`确定要批量最终确认兑换已选择的 ${selectedIds.value.length} 条申请吗？`)) return
  finishBatch(batchFinalApproveExchanges(selectedIds.value, batchComment.value.trim() || '批量最终确认兑换通过。'), '批量最终确认兑换')
}

function batchReject() {
  if (!selectedIds.value.length) return window.alert('请先选择要驳回的兑换申请。')
  if (!batchComment.value.trim()) return window.alert('批量驳回兑换必须填写处理意见。')
  if (!window.confirm(`确定要批量驳回已选择的 ${selectedIds.value.length} 条兑换申请吗？`)) return
  finishBatch(batchFinalRejectExchanges(selectedIds.value, batchComment.value.trim()), '批量驳回兑换')
}
</script>

<template>
  <main class="final-page"><div class="page-content">
    <header class="page-header"><div><p class="eyebrow">A501 · FINAL CONFIRMATION</p><h1>学分兑换管理</h1><p>处理等待管理员最终确认的学分兑换申请。</p></div><RouterLink class="back-link" to="/admin/dashboard">返回</RouterLink></header>
    <nav class="type-tabs" aria-label="最终确认类型"><RouterLink to="/admin/final-confirm">课时最终确认</RouterLink><RouterLink class="active" to="/admin/final-confirm/exchanges">学分兑换最终确认</RouterLink></nav>
    <section class="filters"><label><span>搜索</span><input v-model="keyword" type="search" placeholder="申请编号、学生、团队或任务名称" /></label><label><span>批量处理意见</span><input v-model="batchComment" placeholder="批量驳回时必填" /></label></section>
    <section v-if="batchResult" class="result-card"><strong>{{ batchResult.action }}结果</strong><p>本次处理 {{ batchResult.total }} 条，成功 {{ batchResult.success }} 条，失败 {{ batchResult.failed }} 条。</p><ul v-if="batchResult.failedItems.length"><li v-for="failed in batchResult.failedItems" :key="failed.id">{{ failed.id }}：{{ failed.reason }}</li></ul></section>
    <section class="list-panel"><div class="panel-header"><div><h2>学分兑换最终确认</h2><span>共 {{ items.length }} 条，已选择 {{ selectedIds.length }} 条</span></div><div class="batch-actions"><button class="approve" type="button" @click="batchApprove">批量最终确认兑换</button><button class="reject" type="button" @click="batchReject">批量驳回兑换</button></div></div>
      <div class="table-wrapper"><table><thead><tr><th><input type="checkbox" aria-label="全选兑换申请" :checked="allSelected" :indeterminate.prop="partiallySelected" :disabled="!items.length" @change="toggleAll" /></th><th>兑换申请编号</th><th>申请学生 / 队长</th><th>团队名称</th><th>任务名称</th><th>课时到账</th><th>是否已兑换</th><th>指导老师确认</th><th>申请兑换学分</th><th>当前最终确认状态</th><th>提交时间</th><th>确认类型</th><th>操作</th></tr></thead>
      <tbody><tr v-for="item in items" :key="item.id"><td><input v-model="selectedIds" type="checkbox" :value="item.id" /></td><td><strong>{{ item.exchangeId }}</strong></td><td>{{ item.studentName }}<small>{{ item.studentId }}</small></td><td>{{ item.teamName || '--' }}</td><td>{{ item.taskName || item.projectTitle }}</td><td><StatusTag :status="item.hoursArrived ? 'completed' : 'pending'" :text="item.hoursArrived ? '已到账' : '未到账'" /></td><td><StatusTag :status="item.exchanged ? 'completed' : 'pending'" :text="item.exchanged ? '已兑换' : '未兑换'" /></td><td><StatusTag :status="item.advisorConfirmStatus" :text="['approved','confirmed'].includes(item.advisorConfirmStatus) ? '已确认' : '待确认'" /></td><td>{{ Number(item.estimatedCredits || 0).toFixed(2) }}</td><td><StatusTag :status="item.status" text="待管理员最终确认" /></td><td>{{ item.submitTime }}</td><td>学分兑换最终确认</td><td><RouterLink class="detail-link" :to="`/admin/final-confirm/exchanges/${item.id}`">查看详情</RouterLink></td></tr><tr v-if="!items.length"><td class="empty" colspan="13">暂无待最终确认的学分兑换申请。</td></tr></tbody></table></div>
    </section>
  </div></main>
</template>

<style scoped>
.final-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.page-content{width:min(100%,1380px);margin:auto}.page-header,.panel-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}.page-header{margin-bottom:18px}.page-header h1{margin:0 0 8px}.page-header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800;letter-spacing:.12em}.back-link,.detail-link{color:#2563eb;font-weight:700;text-decoration:none}.back-link{padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.type-tabs{display:flex;gap:8px;margin-bottom:18px;padding:6px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}.type-tabs a{padding:10px 16px;border-radius:8px;color:#475569;text-decoration:none;font-weight:700}.type-tabs .active{color:#1d4ed8;background:#dbeafe}.filters{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;font-weight:700}.filters input{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;font:inherit}.result-card{margin-bottom:18px;padding:16px;border:1px solid #86efac;border-radius:12px;color:#166534;background:#f0fdf4}.result-card p{margin:6px 0}.list-panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-header{align-items:center;padding:18px 20px}.panel-header h2{margin:0 0 4px}.panel-header span{color:#64748b}.batch-actions{display:flex;gap:10px}.batch-actions button{padding:9px 14px;border:0;border-radius:9px;color:#fff;font:inherit;font-weight:700;cursor:pointer}.approve{background:#2563eb}.reject{background:#dc2626}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-top:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc;font-size:13px}input[type=checkbox]{width:17px;height:17px;accent-color:#2563eb}td small{display:block;margin-top:4px;color:#94a3b8}.empty{padding:34px;text-align:center;color:#64748b}@media(max-width:760px){.final-page{padding:24px 14px}.page-header,.panel-header{align-items:stretch;flex-direction:column}.filters{grid-template-columns:1fr}.type-tabs,.batch-actions{flex-wrap:wrap}}
</style>
