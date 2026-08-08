<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { getTaskTypeText } from '../mock/tasks.js'
import { getStudentTask,getTaskTeam } from '../api/taskApi.js';import { adaptTaskEnvelope } from '../adapters/taskAdapter.js';import { getApiErrorMessage } from '../utils/apiFeedback.js'
import { downloadAttachment, getAttachmentErrorMessage, previewAttachment } from '../api/fileApi.js'

const route = useRoute(); const router = useRouter();const task=ref(null);const team=ref(null);onMounted(async()=>{try{const [taskPayload,teamPayload]=await Promise.all([getStudentTask(Number(route.params.id)),getTaskTeam(Number(route.params.id))]);task.value=adaptTaskEnvelope(taskPayload);team.value=teamPayload}catch(error){window.alert(getApiErrorMessage(error,'任务详情加载失败'))}})
const detail = computed(() => ({task:task.value,applyResult:task.value?.myRegistration,isLeader:team.value?.can_submit_result===true}))
const members = computed(() => team.value?.members??[])
const result = computed(() => task.value?.resultSubmission??(team.value?.task_result_submission_id?{id:team.value.task_result_submission_id,status:team.value.task_result_status}:null))
const canSubmitResult = computed(() => detail.value?.isLeader && (!result.value || result.value.status === 'advisor_rejected'))
const resultText = computed(() => ({
  material_submitted: '待指导老师确认成果',
  advisor_rejected: '成果已驳回，可重新提交',
  pending_assignment: '待管理员分配审核老师',
  converted_to_hour_application: '已转入课时认定',
}[result.value?.status] || '未提交'))
function back(){router.push('/student/tasks')}
async function preview(file){try{await previewAttachment(file)}catch(error){window.alert(getAttachmentErrorMessage(error,'preview'))}}
async function download(file){try{await downloadAttachment(file)}catch(error){window.alert(getAttachmentErrorMessage(error,'download'))}}
</script>

<template><main class="page"><div class="content"><template v-if="task">
  <header><div><p class="eyebrow">S102 · TASK DETAIL</p><h1>{{ task.title }}</h1><p>{{ task.taskId }}</p></div><StatusTag :status="task.status" /></header>
  <section class="card"><h2>任务信息</h2><dl class="grid"><div><dt>任务类型</dt><dd>{{ getTaskTypeText(task.taskType) }}</dd></div><div><dt>指导老师</dt><dd>{{ task.advisorName }}</dd></div><div><dt>报名截止时间</dt><dd>{{ task.registrationDeadline }}</dd></div><div><dt>当前任务状态</dt><dd><StatusTag :status="task.status" /></dd></div><div class="wide"><dt>任务说明</dt><dd>{{ task.description }}</dd></div><div class="wide"><dt>成果提交要求</dt><dd>{{ task.resultRequirement }}</dd></div></dl></section>
  <section class="card"><h2>我的参与信息</h2><dl class="grid"><div><dt>报名状态</dt><dd>{{ detail.applyResult?.applyStatus || '--' }}</dd></div><div><dt>筛选结果</dt><dd>{{ detail.applyResult?.selected ? '已选中' : detail.applyResult?.applyStatus === 'not_selected' ? '未选中' : '等待筛选' }}</dd></div><div><dt>队长</dt><dd>{{ task.leaderName || '尚未指定' }}</dd></div><div><dt>我的身份</dt><dd>{{ detail.isLeader ? '队长' : detail.applyResult?.selected ? '成员' : '报名学生' }}</dd></div><div><dt>成果状态</dt><dd><StatusTag :status="result?.status || 'draft'" :text="resultText" /></dd></div><div v-if="result?.advisorComment" class="wide"><dt>指导老师成果意见</dt><dd>{{ result.advisorComment }}</dd></div></dl></section>
  <section class="card"><h2>团队成员</h2><p v-if="!detail.applyResult?.selected" class="muted">被选中后可查看团队成员。</p><div v-else class="members"><span v-for="member in members" :key="member.studentId">{{ member.studentName }}（{{ member.studentId === task.leaderId ? '队长' : '成员' }}）</span></div></section>
  <section class="card"><h2>附件材料</h2><div class="files"><article v-for="file in task.attachments" :key="file.id"><div><strong>{{ file.name }}</strong><small>{{ file.type || '未知类型' }} · {{ file.size || '--' }} · {{ file.uploadedAt || '--' }}</small></div><div><button @click="preview(file)">预览</button><button @click="download(file)">下载</button></div></article><p v-if="!task.attachments?.length" class="muted">暂无附件材料。</p></div></section>
  <div class="actions"><button @click="back">返回</button><RouterLink :to="`/student/tasks/${task.taskId}/result`">查看报名结果</RouterLink><RouterLink :to="`/student/tasks/${task.taskId}/team`">查看团队信息</RouterLink><RouterLink v-if="canSubmitResult" :to="`/student/tasks/${task.taskId}/result-submit`">上传成果</RouterLink></div>
</template><section v-else class="card empty">未找到与当前学生相关的任务。<button @click="back">返回</button></section></div></main></template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,960px);margin:auto}header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}h1{margin:0}header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb!important;font-size:12px;font-weight:800;letter-spacing:.12em}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.wide{grid-column:1/-1}dt{color:#64748b;font-size:13px}dd{margin:5px 0 0;font-weight:600;line-height:1.7}.members{display:flex;flex-wrap:wrap;gap:10px}.members span{padding:9px 12px;border-radius:8px;background:#f1f5f9}.files{display:grid;gap:10px}.files article{display:flex;justify-content:space-between;gap:15px;padding:14px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.files small{display:block;margin-top:5px;color:#64748b}.files article>div:last-child{display:flex;gap:8px}.files button{padding:7px 10px;border:1px solid #bfdbfe;border-radius:8px;color:#2563eb;background:#fff;font-weight:700}.muted,.empty{color:#64748b}.actions{display:flex;justify-content:flex-end;gap:10px}.actions a,.actions button,.empty button{padding:10px 16px;border:1px solid #cbd5e1;border-radius:9px;color:#2563eb;background:#fff;font:inherit;font-weight:700;text-decoration:none}.empty{text-align:center}@media(max-width:650px){.page{padding:24px 14px}header,.files article{flex-direction:column}.grid{grid-template-columns:1fr}.wide{grid-column:auto}.actions{flex-wrap:wrap}}
</style>
