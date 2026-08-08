<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import RuleFilePanel from '../components/RuleFilePanel.vue'
import { approveExchangeByAdvisor, getAdvisorExchange, rejectExchangeByAdvisor } from '../api/exchangeApi.js'
import { adaptExchangeEnvelope } from '../adapters/exchangeAdapter.js'
import { downloadAttachment, getAttachmentErrorMessage, previewAttachment } from '../api/fileApi.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const route = useRoute(); const router = useRouter()
const opinion = ref(''); const feedback = ref('')
const item = ref(null)
onMounted(async()=>{try{item.value=adaptExchangeEnvelope(await getAdvisorExchange(Number(route.params.id)))}catch(error){window.alert(getApiErrorMessage(error,'兑换申请详情加载失败'))}})
const allocatedHours = computed(() => item.value?.memberDistributions?.reduce((sum, member) => sum + Number(member.allocatedHours || 0), 0) || 0)
const allocatedCredits = computed(() => item.value?.memberDistributions?.reduce((sum, member) => sum + Number(member.allocatedCredits || 0), 0) || 0)
const canProcess = computed(() => item.value?.status === 'submitted')
function validate() { if (!item.value?.memberDistributions?.length) return '成员分配表不能为空。'; if (Math.abs(allocatedHours.value - Number(item.value.finalHours || 0)) > .000001) return '成员分配课时总和必须等于项目最终认定课时。'; return '' }
async function approve() { const error=validate(); if(error){feedback.value=error;return window.alert(error)};try{await approveExchangeByAdvisor(item.value.id,{comment:opinion.value.trim()});window.alert('确认通过，申请已进入管理员最终确认。');goBack()}catch(error){window.alert(getApiErrorMessage(error,'确认兑换失败'))} }
async function reject() { if(!opinion.value.trim()){feedback.value='驳回时必须填写确认意见。';return window.alert(feedback.value)};try{await rejectExchangeByAdvisor(item.value.id,{comment:opinion.value.trim()});window.alert('申请已驳回并退回学生端。');goBack()}catch(error){window.alert(getApiErrorMessage(error,'驳回兑换失败'))} }
function goBack(){router.push('/teacher/confirm/exchanges')}
async function previewFile(file){try{await previewAttachment(file)}catch(error){window.alert(getAttachmentErrorMessage(error,'附件预览失败，请稍后重试。'))}}async function downloadFile(file){try{await downloadAttachment(file)}catch(error){window.alert(getAttachmentErrorMessage(error,'附件下载失败，请稍后重试。'))}}
</script>

<template><main class="page"><div class="content"><template v-if="item">
<header class="header"><div><p class="eyebrow">T602 · EXCHANGE DETAIL</p><h1>{{ item.projectTitle }}</h1><p>{{ item.exchangeId }}</p></div><StatusTag :status="item.status" /></header>
<RuleFilePanel rule-type="credit_rule" title="学分兑换规则" description="确认兑换申请时，请参考当前学分兑换规则。" />
  <section class="card"><h2>团队信息</h2><dl class="grid"><div><dt>团队名称</dt><dd>{{ item.teamName || '--' }}</dd></div><div><dt>成员数量</dt><dd>{{ item.memberDistributions?.length || 0 }} 人</dd></div></dl></section>
  <section class="card"><h2>队长信息</h2><dl class="grid"><div><dt>队长姓名</dt><dd>{{ item.captainName || item.studentName }}</dd></div><div><dt>学号</dt><dd>{{ item.studentId }}</dd></div></dl></section>
  <section class="card"><h2>任务信息</h2><dl class="grid"><div><dt>项目名称</dt><dd>{{ item.projectTitle }}</dd></div><div><dt>任务名称</dt><dd>{{ item.taskName || '--' }}</dd></div><div><dt>申请来源</dt><dd>{{ item.sourceText || '--' }}</dd></div><div><dt>项目最终认定课时</dt><dd>{{ item.finalHours }} 课时</dd></div></dl></section>
  <section class="card"><h2>成员学时 / 学分分配表</h2><div class="table-wrap"><table><thead><tr><th>成员姓名</th><th>学号</th><th>角色</th><th>分配课时</th><th>分配学分</th><th>备注</th></tr></thead><tbody><tr v-for="member in item.memberDistributions" :key="member.studentId"><td>{{ member.studentName }}</td><td>{{ member.studentId }}</td><td>{{ member.role==='captain'?'队长':'成员' }}</td><td>{{ member.allocatedHours }}</td><td>{{ Number(member.allocatedCredits||0).toFixed(2) }}</td><td>{{ member.remark||'--' }}</td></tr><tr v-if="!item.memberDistributions?.length"><td class="empty" colspan="6">成员分配表为空。</td></tr></tbody></table></div><div class="summary"><span>成员分配课时总和：<strong>{{ allocatedHours }}</strong></span><span>成员分配学分总和：<strong>{{ allocatedCredits.toFixed(2) }}</strong></span></div></section>
  <section class="card"><h2>分配证明材料</h2><div class="files"><article v-for="file in item.proofMaterials" :key="file.id||file.name"><div><strong>{{ file.name }}</strong><small>{{ file.type||'未知类型' }} · {{ file.uploadedAt||'--' }}</small></div><div><button @click="previewFile(file)">预览</button><button @click="downloadFile(file)">下载</button></div></article><p v-if="!item.proofMaterials?.length" class="empty">暂无证明材料。</p></div></section>
  <section class="card"><h2>队长申请说明</h2><p>{{ item.applyReason || '无' }}</p></section>
  <section class="card"><h2>确认信息</h2><dl class="grid status-grid"><div><dt>当前状态</dt><dd><StatusTag :status="item.status" /></dd></div><div><dt>确认时间</dt><dd>{{ item.advisorConfirmTime || '--' }}</dd></div><div v-if="!canProcess"><dt>指导老师确认意见</dt><dd>{{ item.advisorComment || '无' }}</dd></div></dl><template v-if="canProcess"><label for="opinion">指导老师确认意见</label><textarea id="opinion" v-model="opinion" rows="5" placeholder="请输入确认意见；驳回时必填。"></textarea></template><p v-if="feedback" class="feedback">{{ feedback }}</p></section>
  <div class="actions"><button class="back" @click="goBack">返回</button><button class="reject" :disabled="!canProcess" @click="reject">驳回申请</button><button class="approve" :disabled="!canProcess" @click="approve">确认通过</button></div>
</template><section v-else class="card empty"><h1>未找到兑换确认事项</h1><button class="back" @click="goBack">返回</button></section></div></main></template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,980px);margin:auto}.header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}.header h1{margin:0}.header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb!important;font-size:12px;font-weight:800;letter-spacing:.12em}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px;font-size:19px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.grid dt{color:#64748b;font-size:13px}.grid dd{margin:5px 0 0;font-weight:600}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc}.summary{display:flex;gap:28px;margin-top:18px;padding:16px;border-radius:10px;background:#f8fafc}.files{display:grid;gap:10px}.files article{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:14px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.files small{display:block;margin-top:5px;color:#64748b}.files article>div:last-child{display:flex;gap:8px}.files button{padding:7px 10px;border:1px solid #bfdbfe;border-radius:8px;color:#1d4ed8;background:#fff;font-weight:700}.status-grid{margin-bottom:18px}label{font-weight:700}textarea{width:100%;margin-top:10px;padding:11px;border:1px solid #cbd5e1;border-radius:9px;resize:vertical;font:inherit}.feedback{color:#b91c1c}.actions{display:flex;justify-content:flex-end;gap:10px}.actions button,.empty button{padding:10px 18px;border-radius:9px;font:inherit;font-weight:700;cursor:pointer}.back{border:1px solid #cbd5e1;background:#fff}.reject{border:0;color:#fff;background:#dc2626}.approve{border:0;color:#fff;background:#2563eb}button:disabled{opacity:.5;cursor:not-allowed}.empty{text-align:center;color:#64748b}@media(max-width:650px){.page{padding:24px 14px}.header,.files article{flex-direction:column}.grid{grid-template-columns:1fr}.summary,.actions{flex-wrap:wrap}}
</style>
