<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ReviewActionBar from '../components/ReviewActionBar.vue'
import StatusTag from '../components/StatusTag.vue'
import {
  APPLICATION_STATUS,
  currentReviewerId,
  getApplications,
  reviewerApprove,
  reviewerModifiedApprove,
  reviewerReject,
} from '../mock/applications.js'
import { approveApplicationByReviewer, getReviewerApplication, modifiedApproveApplication, rejectApplicationByReviewer } from '../api/applicationApi.js'
import { adaptApplicationEnvelope } from '../adapters/applicationAdapter.js'
import { getApiErrorMessage, hasServerAction } from '../utils/apiFeedback.js'

const route = useRoute(); const router = useRouter()
const item = ref(null)
const readonly = computed(() => route.name === 'reviewer-review-record-detail')
const recognizedHours = ref('')
const opinion = ref(item.value?.reviewComment ?? '')
const feedback = ref({ type: '', message: '' })
const hoursChanged = computed(() => item.value
  ? Number(recognizedHours.value) !== Number(item.value.requestedHours)
  : false)
async function loadItem(){try{item.value=adaptApplicationEnvelope(await getReviewerApplication(Number(route.params.id)));recognizedHours.value=item.value.reviewerSuggestedHours??item.value.requestedHours??'';opinion.value=item.value.reviewComment??''}catch(error){window.alert(getApiErrorMessage(error,'审核详情加载失败'))}}
onMounted(loadItem)

function validateRecognizedHours() {
  if (recognizedHours.value === '' || !Number.isFinite(Number(recognizedHours.value)) || Number(recognizedHours.value) <= 0) return '审核认定课时必须为大于 0 的数字'
  return ''
}
function showError(message) { feedback.value = { type: 'error', message }; window.alert(message) }
async function runAction(request,body,message){try{await request(item.value.id,body);await loadItem();feedback.value={type:'success',message};window.alert(message)}catch(error){showError(getApiErrorMessage(error))}}
function approve() { const error = validateRecognizedHours(); if (error) return showError(error); if (hoursChanged.value) return showError('认定课时已修改，请使用“修改课时后审核通过”'); if(!hasServerAction(item.value.actions,['approve','reviewer_approve'],item.value.status==='pending_review'))return;return runAction(approveApplicationByReviewer,{comment:opinion.value.trim()},'审核通过成功，申请已进入管理员最终确认环节。') }
function approveWithChange() { const error = validateRecognizedHours(); if (error) return showError(error); if (!hoursChanged.value) return showError('认定课时未修改，请使用“审核通过”'); if (!opinion.value.trim()) return showError('请填写修改课时原因或审核意见');return runAction(modifiedApproveApplication,{reviewer_suggested_hours:Number(recognizedHours.value),comment:opinion.value.trim()},'已修改课时并审核通过，申请已进入管理员最终确认环节。') }
function reject() { if (!opinion.value.trim()) return showError('请填写驳回原因');return runAction(rejectApplicationByReviewer,{comment:opinion.value.trim()},'已驳回') }
function preview() { window.alert('当前为 Mock 附件预览，真实预览需后端文件服务支持。') } function download() { window.alert('当前为 Mock 附件下载，真实下载需后端文件服务支持。') }
function goBack() { router.push(readonly.value ? '/reviewer/review-records' : '/reviewer/review-tasks') }
</script>

<template><main class="detail-page"><div class="detail-content"><template v-if="item">
  <header class="page-header"><div><p class="eyebrow">REVIEW DETAIL</p><h1>{{ item.title }}</h1><p>{{ item.applyTypeText }}</p></div><StatusTag :status="item.status" /></header>
  <div v-if="readonly" class="readonly-notice">这是历史审核记录，仅供查看，不允许再次修改。</div>
  <section class="card"><h2>学生信息</h2><dl class="info-grid"><div><dt>姓名</dt><dd>{{ item.studentName }}</dd></div><div><dt>学号</dt><dd>{{ item.studentId }}</dd></div><div><dt>申请人身份</dt><dd>{{ item.captainId === item.currentUserId ? '队长' : '成员' }}</dd></div><div><dt>当前流程</dt><dd>审核老师审核</dd></div></dl></section>
  <section class="card"><h2>申请信息</h2><dl class="info-grid"><div><dt>申请编号</dt><dd>{{ item.id }}</dd></div><div><dt>申请来源</dt><dd>{{ item.sourceText }}</dd></div><div><dt>申请类型</dt><dd>{{ item.applyTypeText }}</dd></div><div><dt>原申请课时</dt><dd>{{ item.requestedHours }} 小时</dd></div><div v-if="item.taskId"><dt>关联任务</dt><dd>{{ item.taskTitle }}（{{ item.taskId }}）</dd></div><div><dt>分配审核老师</dt><dd>{{ item.reviewer?.name || '--' }}<template v-if="item.reviewer?.direction"> · {{ item.reviewer.direction }}</template></dd></div><div><dt>管理员受理时间</dt><dd>{{ item.adminAcceptTime }}</dd></div></dl></section>
  <section class="card"><h2>团队成员</h2><div class="table-wrapper"><table><thead><tr><th>姓名</th><th>学号</th><th>学院</th><th>专业</th><th>角色</th></tr></thead><tbody><tr v-for="member in item.members" :key="member.id"><td>{{ member.name }}</td><td>{{ member.studentId }}</td><td>{{ member.college || '--' }}</td><td>{{ member.major || '--' }}</td><td>{{ member.role === 'captain' ? '队长' : '成员' }}</td></tr></tbody></table></div></section>
  <section class="card"><h2>前序处理意见</h2><div class="opinion-block"><strong>指导老师确认意见</strong><p>{{ item.mainAdvisor?.name || '--' }} · {{ item.mainAdvisor?.department || '--' }}</p><p>{{ item.advisorComment || '未填写确认意见' }}</p></div><div class="opinion-block"><strong>管理员受理意见</strong><p>{{ item.adminAcceptComment || '未填写受理意见' }}</p></div></section>
  <section class="card"><h2>学生上传材料</h2><div v-if="item.attachments.length" class="attachments"><article v-for="file in item.attachments" :key="file.id"><div><h3>{{ file.name }}</h3><small>{{ file.type }}<template v-if="file.uploadedAt"> · {{ file.uploadedAt }}</template></small><p>{{ file.description }}</p></div><div><button type="button" @click="preview(file)">预览</button><button type="button" @click="download(file)">下载</button></div></article></div><p v-else class="empty">暂无上传材料</p></section>
  <section class="card review-form"><div class="hours-reference"><span>原申请课时</span><strong>{{ item.requestedHours }} 小时</strong></div><label for="recognized-hours">审核认定课时</label><input id="recognized-hours" v-model="recognizedHours" type="number" min="1" step="1" :readonly="readonly" /><p v-if="!readonly" class="hours-hint">{{ hoursChanged ? '认定课时已修改，将使用“修改课时后审核通过”。' : '认定课时与原申请一致，可直接审核通过。' }}</p><label for="review-opinion">审核意见</label><textarea id="review-opinion" v-model="opinion" rows="5" :readonly="readonly" placeholder="请输入审核意见；修改课时或驳回时必须填写。"></textarea><p v-if="readonly && item.reviewTime" class="review-time">审核时间：{{ item.reviewTime }}</p><p v-if="feedback.message" class="feedback" :class="`feedback--${feedback.type}`">{{ feedback.message }}</p></section>
  <ReviewActionBar v-if="!readonly && hasServerAction(item.actions,['approve','reviewer_approve'],item.status === 'pending_review')" :approve-text="hoursChanged ? '修改课时并通过' : '审核通过'" reject-text="审核驳回" @approve="hoursChanged ? approveWithChange() : approve()" @reject="reject"><template #before><button class="back-button" type="button" @click="goBack">返回</button></template></ReviewActionBar>
  <div v-else class="readonly-actions"><button class="back-button" type="button" @click="goBack">返回</button></div>
</template><section v-else class="not-found"><h1>未找到审核任务</h1><button class="back-button" @click="goBack">返回</button></section></div></main></template>

<style scoped>
.detail-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.detail-content{width:min(100%,960px);margin:0 auto}.page-header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}.page-header h1{margin:0 0 8px}.page-header p{margin:0;color:#64748b}.readonly-notice{margin-bottom:18px;padding:12px 16px;border-radius:9px;color:#1d4ed8;background:#eff6ff}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px;font-size:19px}.info-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.info-grid dt{color:#64748b;font-size:13px}.info-grid dd{margin:5px 0 0;font-weight:600}.description{padding-top:14px;border-top:1px solid #e2e8f0;color:#475569;line-height:1.7}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left}th{background:#f8fafc}.opinion-block+ .opinion-block{margin-top:16px;padding-top:16px;border-top:1px solid #e2e8f0}.opinion-block p{margin:7px 0 0;color:#475569}.attachments{display:grid;gap:10px}.attachments article{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:14px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.attachments h3{margin:0;font-size:15px}.attachments small{color:#64748b}.attachments p{margin:5px 0 0;color:#475569}.attachments article>div:last-child{display:flex;gap:8px}.attachments button{padding:7px 10px;border:1px solid #bfdbfe;border-radius:8px;color:#1d4ed8;background:#fff;font-weight:700;cursor:pointer}.empty{text-align:center;color:#64748b}.review-form label{display:block;margin-bottom:8px;font-weight:700}.review-form input,.review-form textarea{width:100%;margin-bottom:18px;padding:10px 11px;border:1px solid #cbd5e1;border-radius:9px;font:inherit}.review-form textarea{resize:vertical}.review-form [readonly]{color:#475569;background:#f8fafc}.review-time{color:#64748b}.feedback{padding:10px;border-radius:8px}.feedback--error{color:#b91c1c;background:#fef2f2}.feedback--success{color:#166534;background:#f0fdf4}.back-button,.change-button{padding:10px 18px;border-radius:10px;font:inherit;font-weight:700;cursor:pointer}.back-button{border:1px solid #cbd5e1;background:#fff}.change-button{border:1px solid #0f766e;color:#fff;background:#0f766e}.readonly-actions{display:flex;justify-content:flex-end}.not-found{padding:40px;background:#fff;text-align:center}@media(max-width:650px){.detail-page{padding:24px 14px}.info-grid{grid-template-columns:1fr}.attachments article{align-items:flex-start;flex-direction:column}}
.hours-reference{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;padding:12px 14px;border-radius:9px;background:#f8fafc}.hours-reference span{color:#64748b}.hours-hint{margin:-10px 0 18px;color:#64748b;font-size:13px}
</style>
