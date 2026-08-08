<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { getStudentExchange } from '../api/exchangeApi.js'
import { adaptExchangeEnvelope } from '../adapters/exchangeAdapter.js'
import { downloadAttachment, getAttachmentErrorMessage, previewAttachment } from '../api/fileApi.js'
import { currentUser as authCurrentUser } from '../stores/authStore.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const EXCHANGE_STATUS={COMPLETED:'completed',FINAL_APPROVED:'final_approved',PENDING_CONFIRMATION:'submitted',FINAL_REJECTED:'final_rejected',ADVISOR_REJECTED:'advisor_rejected',REJECTED:'rejected'}
const PENDING_CREDIT_STATUSES=['submitted','advisor_approved','pending_admin_final']

const route = useRoute()
const router = useRouter()
const item=ref(null)
const currentStudentId=computed(()=>Number(authCurrentUser.value?.student?.id))
const currentStudentNo=computed(()=>authCurrentUser.value?.student?.student_no??authCurrentUser.value?.student?.studentId)
const isCaptain=computed(()=>Number(item.value?.leaderStudentId)===currentStudentId.value||Number(item.value?.applicant?.id)===currentStudentId.value)
const personalDistribution=computed(()=>item.value?.memberDistributions?.find((member)=>member.studentId===currentStudentNo.value))
onMounted(async()=>{try{item.value=adaptExchangeEnvelope(await getStudentExchange(Number(route.params.id)))}catch(error){window.alert(getApiErrorMessage(error,'兑换详情加载失败'))}})
const credited = computed(() => [EXCHANGE_STATUS.COMPLETED, EXCHANGE_STATUS.FINAL_APPROVED].includes(item.value?.status))
const pending = computed(() => PENDING_CREDIT_STATUSES.includes(item.value?.status))
const rejected = computed(() => [EXCHANGE_STATUS.FINAL_REJECTED, EXCHANGE_STATUS.ADVISOR_REJECTED, EXCHANGE_STATUS.REJECTED].includes(item.value?.status))
const resultText = computed(() => credited.value ? '学分已到账' : item.value?.status === EXCHANGE_STATUS.PENDING_CONFIRMATION ? '待指导老师确认' : pending.value ? '待管理员最终确认' : rejected.value ? '兑换已驳回' : '')
async function fileAction(action, file) { try { await (action === '预览' ? previewAttachment(file) : downloadAttachment(file)) } catch (error) { window.alert(getAttachmentErrorMessage(error, action === '预览' ? 'preview' : 'download')) } }
function goBack() { router.push('/student/credit-exchange-records') }
</script>

<template><main class="detail-page"><div class="content"><template v-if="item">
  <header class="page-header"><div><p class="eyebrow">EXCHANGE RESULT</p><h1>{{ item.projectTitle }}</h1><p>{{ item.exchangeId }}</p></div><StatusTag :status="item.status" :text="resultText" /></header>
  <section v-if="credited" class="result-banner success"><strong>学分已到账</strong><p>本次到账 {{ Number(personalDistribution?.allocatedCredits || 0).toFixed(2) }} 学分，到账时间：{{ item.finalConfirmTime || '--' }}</p></section>
  <section v-else-if="pending" class="result-banner pending"><strong>{{ resultText }}</strong><p>{{ item.status === EXCHANGE_STATUS.PENDING_CONFIRMATION ? '申请已提交，请等待指导老师确认。' : '指导老师已确认通过，请等待管理员最终确认。' }}</p></section>
  <section v-else-if="rejected" class="result-banner rejected"><strong>兑换已驳回</strong><p>驳回原因：{{ item.status === EXCHANGE_STATUS.ADVISOR_REJECTED ? (item.advisorComment || '未填写原因') : (item.finalComment || '未填写原因') }}</p></section>
  <section class="card"><h2>项目与兑换信息</h2><dl class="grid"><div><dt>项目名称</dt><dd>{{ item.projectTitle }}</dd></div><div><dt>队长姓名</dt><dd>{{ item.captainName || item.studentName }}</dd></div><div><dt>本人分配课时</dt><dd>{{ Number(personalDistribution?.allocatedHours || 0) }} 课时</dd></div><div><dt>本人分配学分</dt><dd>{{ Number(personalDistribution?.allocatedCredits || 0).toFixed(2) }} 学分</dd></div><div><dt>兑换规则</dt><dd>{{ item.creditRule?.text || '每 8 课时兑换 1 学分' }}</dd></div><div><dt>到账时间</dt><dd>{{ credited ? (item.finalConfirmTime || '--') : '--' }}</dd></div></dl></section>
  <section class="card"><h2>处理信息</h2><dl class="grid"><div><dt>指导老师确认状态</dt><dd><StatusTag :status="item.advisorConfirmStatus" /></dd></div><div><dt>指导老师确认意见</dt><dd>{{ item.advisorComment || '无' }}</dd></div><div><dt>管理员最终确认状态</dt><dd><StatusTag :status="item.status" :text="resultText" /></dd></div><div><dt>管理员最终确认意见</dt><dd>{{ item.finalComment || '无' }}</dd></div></dl></section>
  <section class="card"><h2>证明材料</h2><div class="files"><article v-for="file in item.proofMaterials" :key="file.id || file.name"><div><strong>{{ file.name }}</strong><small>{{ file.type || '未知类型' }} · {{ file.uploadedAt || '--' }}</small></div><div><button @click="fileAction('预览', file)">预览</button><button @click="fileAction('下载', file)">下载</button></div></article><p v-if="!item.proofMaterials?.length" class="empty">暂无证明材料。</p></div></section>
  <section class="card"><h2>{{ isCaptain ? '成员学时 / 学分分配表' : '我的学时 / 学分分配' }}</h2><div class="table-wrap"><table><thead><tr><th>成员姓名</th><th>学号</th><th>成员角色</th><th>分配课时</th><th>分配学分</th><th>备注</th></tr></thead><tbody><tr v-for="member in (isCaptain ? item.memberDistributions : (personalDistribution ? [personalDistribution] : []))" :key="member.studentId"><td>{{ member.studentName }}</td><td>{{ member.studentId }}</td><td>{{ member.role === 'captain' ? '队长' : '成员' }}</td><td>{{ member.allocatedHours }}</td><td>{{ Number(member.allocatedCredits || 0).toFixed(2) }}</td><td>{{ member.remark || '--' }}</td></tr><tr v-if="!item.memberDistributions?.length"><td class="empty" colspan="6">暂无成员分配数据。</td></tr></tbody></table></div></section>
  <div class="actions"><button @click="goBack">返回</button></div>
</template><section v-else class="card empty"><h1>未找到兑换记录</h1><button @click="goBack">返回</button></section></div></main></template>

<style scoped>
.detail-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,960px);margin:auto}.page-header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}.page-header h1{margin:0}.page-header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800;letter-spacing:.12em}.result-banner{margin-bottom:18px;padding:18px;border-radius:12px}.result-banner strong{font-size:18px}.result-banner p{margin:6px 0 0}.success{color:#166534;background:#dcfce7}.pending{color:#92400e;background:#fef3c7}.rejected{color:#b91c1c;background:#fee2e2}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px;font-size:19px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.grid dt{color:#64748b;font-size:13px}.grid dd{margin:5px 0 0;font-weight:600}.files{display:grid;gap:10px}.files article{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:14px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.files small{display:block;margin-top:5px;color:#64748b}.files article>div:last-child{display:flex;gap:8px}.files button{padding:7px 10px;border:1px solid #bfdbfe;border-radius:8px;color:#1d4ed8;background:#fff;font-weight:700}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc}.empty{text-align:center;color:#64748b}.actions{display:flex;justify-content:flex-end}.actions button,.empty button{padding:10px 18px;border:1px solid #cbd5e1;border-radius:9px;background:#fff;font:inherit;font-weight:700}@media(max-width:650px){.detail-page{padding:24px 14px}.page-header,.files article{align-items:flex-start;flex-direction:column}.grid{grid-template-columns:1fr}}
</style>
