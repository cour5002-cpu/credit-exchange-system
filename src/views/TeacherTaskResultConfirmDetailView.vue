<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { TASK_RESULT_STATUS, approveTaskResult, getTaskResultById, rejectTaskResult } from '../mock/taskResults.js'
import { getTaskById, getTaskTypeText } from '../mock/tasks.js'

const route = useRoute(); const router = useRouter(); const advisorId = 'T001'
const comment = ref('')
const result = computed(() => { const item = getTaskResultById(route.params.id); return item?.advisorId === advisorId ? item : null })
const task = computed(() => result.value ? getTaskById(result.value.taskId) : null)
const pending = computed(() => result.value?.status === TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM)
function back(){router.push('/teacher/confirm/results')}
function preview(){window.alert('当前为 Mock 附件预览，真实预览需后端文件服务支持。')}
function download(){window.alert('当前为 Mock 附件下载，真实下载需后端文件服务支持。')}
function approve(){if(!pending.value)return window.alert('该成果已处理，不能重复确认。');if(!approveTaskResult(result.value.resultId,comment.value))return window.alert('成果确认失败。');window.alert('成果确认通过，学生可基于该成果发起课时申请。');back()}
function reject(){if(!pending.value)return window.alert('该成果已处理，不能重复确认。');if(!comment.value.trim())return window.alert('驳回成果时必须填写确认意见。');if(!rejectTaskResult(result.value.resultId,comment.value))return window.alert('成果驳回失败。');window.alert('成果已驳回，队长可修改后重新提交。');back()}
</script>

<template><main class="page"><div class="content"><template v-if="result">
  <header><div><p class="eyebrow">T107 · RESULT DETAIL</p><h1>任务成果确认详情</h1><p>{{ result.resultId }}</p></div><StatusTag :status="result.status" /></header>
  <section class="card"><h2>任务基本信息</h2><dl class="grid"><div><dt>任务名称</dt><dd>{{ result.taskTitle }}</dd></div><div><dt>任务编号</dt><dd>{{ result.taskId }}</dd></div><div><dt>任务类型</dt><dd>{{ task ? getTaskTypeText(task.taskType) : '--' }}</dd></div><div><dt>指导老师</dt><dd>{{ result.advisorName }}</dd></div><div><dt>成果提交时间</dt><dd>{{ result.submitTime }}</dd></div><div><dt>当前成果状态</dt><dd><StatusTag :status="result.status" /></dd></div></dl></section>
  <section class="card"><h2>队长与团队成员</h2><dl class="grid"><div><dt>队长姓名</dt><dd>{{ result.leaderName }}</dd></div><div><dt>队长学号</dt><dd>{{ result.leaderId }}</dd></div></dl><div class="table-wrap"><table><thead><tr><th>姓名</th><th>学号</th><th>学院</th><th>专业</th><th>角色</th></tr></thead><tbody><tr v-for="member in result.teamMembers" :key="member.studentId"><td>{{ member.name }}</td><td>{{ member.studentId }}</td><td>{{ member.college || '--' }}</td><td>{{ member.major || '--' }}</td><td>{{ member.role === 'captain' ? '队长' : '成员' }}</td></tr></tbody></table></div></section>
  <section class="card"><h2>成果说明</h2><p class="description">{{ result.resultDescription }}</p></section>
  <section class="card"><h2>成果材料</h2><div class="files"><article v-for="file in result.resultMaterials" :key="file.id"><div><strong>{{ file.name || file.fileName }}</strong><small>{{ file.type || file.fileType || '未知类型' }} · {{ file.size || file.fileSize || '--' }} · {{ file.uploadedAt || file.uploadTime || '--' }}</small></div><div><button @click="preview">预览</button><button @click="download">下载</button></div></article><p v-if="!result.resultMaterials?.length" class="muted">暂无附件材料</p></div></section>
  <section class="card"><h2>证明材料</h2><div class="files"><article v-for="file in result.proofMaterials" :key="file.id"><div><strong>{{ file.name || file.fileName }}</strong><small>{{ file.type || file.fileType || '未知类型' }} · {{ file.size || file.fileSize || '--' }} · {{ file.uploadedAt || file.uploadTime || '--' }}</small></div><div><button @click="preview">预览</button><button @click="download">下载</button></div></article><p v-if="!result.proofMaterials?.length" class="muted">暂无附件材料</p></div></section>
  <section class="card"><h2>指导老师确认意见</h2><textarea v-model="comment" rows="5" :disabled="!pending" placeholder="请输入确认意见；驳回时必填。"></textarea><p v-if="!pending && result.advisorComment" class="processed">已处理意见：{{ result.advisorComment }}（{{ result.advisorConfirmTime }}）</p></section>
  <div class="actions"><button class="back-button" @click="back">返回</button><button class="reject" :disabled="!pending" @click="reject">驳回成果</button><button class="approve" :disabled="!pending" @click="approve">确认通过</button></div>
</template><section v-else class="card empty">成果不存在，或不属于当前指导老师。<button @click="back">返回</button></section></div></main></template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,980px);margin:auto}header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}h1{margin:0}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800;letter-spacing:.12em}header p,.muted{color:#64748b}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}dt{color:#64748b;font-size:13px}dd{margin:5px 0 0;font-weight:600}.table-wrap{overflow-x:auto;margin-top:18px}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left}th{background:#f8fafc}.description{white-space:pre-wrap;line-height:1.8}.files{display:grid;gap:10px}.files article{display:flex;justify-content:space-between;gap:15px;padding:14px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.files small{display:block;margin-top:5px;color:#64748b}.files article>div:last-child{display:flex;gap:8px}.files button{padding:7px 10px;border:1px solid #bfdbfe;border-radius:8px;color:#2563eb;background:#fff;font-weight:700}textarea{width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:9px;font:inherit}.processed{padding:12px;border-radius:8px;background:#f1f5f9}.actions{display:flex;justify-content:flex-end;gap:10px}.actions button,.empty button{padding:10px 18px;border-radius:9px;font:inherit;font-weight:700}.back-button{border:1px solid #cbd5e1;background:#fff}.reject{border:1px solid #fecaca;color:#b91c1c;background:#fff}.approve{border:0;color:#fff;background:#2563eb}.actions button:disabled{opacity:.5}.empty{text-align:center}@media(max-width:650px){.page{padding:24px 14px}header,.files article{flex-direction:column}.grid{grid-template-columns:1fr}.actions{flex-wrap:wrap}}
</style>
