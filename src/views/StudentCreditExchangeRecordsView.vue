<script setup>
import { computed, onMounted, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { getStudentExchange, getStudentExchanges } from '../api/exchangeApi.js'
import { adaptExchangeEnvelope, adaptExchangeList } from '../adapters/exchangeAdapter.js'
import { currentUser as authCurrentUser } from '../stores/authStore.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const EXCHANGE_STATUS={COMPLETED:'completed',FINAL_APPROVED:'final_approved',PENDING_CONFIRMATION:'submitted',PENDING_FINAL_CONFIRM:'pending_admin_final',PENDING_DISTRIBUTION_CONFIRM:'advisor_approved',FINAL_REJECTED:'final_rejected',ADVISOR_REJECTED:'advisor_rejected',REJECTED:'rejected'}

const remoteItems=ref([])
const currentStudentNo=computed(()=>authCurrentUser.value?.student?.student_no??authCurrentUser.value?.student?.studentId)
const items=computed(()=>[...remoteItems.value].sort((a,b)=>String(b.submitTime??b.updatedAt??'').localeCompare(String(a.submitTime??a.updatedAt??''))))
function personalDistribution(item){return item.memberDistributions?.find((member)=>member.studentId===currentStudentNo.value)||{}}
onMounted(async()=>{try{const summaries=adaptExchangeList(await getStudentExchanges({page_size:100}));remoteItems.value=summaries;await Promise.allSettled(summaries.map(async(item)=>{const detail=adaptExchangeEnvelope(await getStudentExchange(item.id));remoteItems.value=remoteItems.value.map((current)=>current.id===item.id?detail:current)}))}catch(error){window.alert(getApiErrorMessage(error,'兑换记录加载失败'))}})
function statusText(status) {
  if ([EXCHANGE_STATUS.COMPLETED, EXCHANGE_STATUS.FINAL_APPROVED].includes(status)) return '学分已到账'
  if (status === EXCHANGE_STATUS.PENDING_CONFIRMATION) return '待指导老师确认'
  if ([EXCHANGE_STATUS.PENDING_FINAL_CONFIRM, EXCHANGE_STATUS.PENDING_DISTRIBUTION_CONFIRM].includes(status)) return '待管理员最终确认'
  if ([EXCHANGE_STATUS.FINAL_REJECTED, EXCHANGE_STATUS.ADVISOR_REJECTED, EXCHANGE_STATUS.REJECTED].includes(status)) return '兑换已驳回'
  return ''
}
</script>

<template><main class="records-page"><div class="page-content">
  <header class="page-header"><div><p class="eyebrow">S603 · EXCHANGE RECORDS</p><h1>我的兑换记录</h1><p>查看学分兑换进度、最终确认结果和到账信息。</p></div><RouterLink class="back-link" to="/student/dashboard">返回</RouterLink></header>
  <section class="list-panel"><div class="panel-header"><h2>兑换申请记录</h2><span>共 {{ items.length }} 条</span></div><div class="table-wrapper"><table><thead><tr><th>项目名称</th><th>队长姓名</th><th>本人分配课时</th><th>本人分配学分</th><th>兑换状态</th><th>到账时间</th><th>操作</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><strong>{{ item.projectTitle }}</strong><small>{{ item.exchangeId }}</small></td><td>{{ item.captainName || item.studentName }}</td><td>{{ Number(personalDistribution(item).allocatedHours || 0) }} 课时</td><td>{{ Number(personalDistribution(item).allocatedCredits || 0).toFixed(2) }} 学分</td><td><StatusTag :status="item.status" :text="statusText(item.status)" /></td><td>{{ [EXCHANGE_STATUS.COMPLETED, EXCHANGE_STATUS.FINAL_APPROVED].includes(item.status) ? (item.finalConfirmTime || '--') : '--' }}</td><td><RouterLink class="detail-link" :to="`/student/credit-exchange-records/${item.id}`">查看详情</RouterLink></td></tr><tr v-if="!items.length"><td class="empty" colspan="7">暂无学分兑换记录。</td></tr></tbody></table></div></section>
</div></main></template>

<style scoped>
.records-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.page-content{width:min(100%,1120px);margin:auto}.page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:22px}.page-header h1{margin:0 0 8px}.page-header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800;letter-spacing:.12em}.back-link,.detail-link{color:#2563eb;font-weight:700;text-decoration:none}.back-link{padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.list-panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px}.panel-header h2{margin:0}.panel-header span{color:#64748b}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:13px 14px;border-top:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{color:#475569;background:#f8fafc;font-size:13px}.empty{padding:34px;text-align:center;color:#64748b}@media(max-width:650px){.records-page{padding:24px 14px}.page-header{flex-direction:column}}
</style>
