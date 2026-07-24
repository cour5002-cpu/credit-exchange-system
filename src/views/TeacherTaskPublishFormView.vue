<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AttachmentNotice from '../components/AttachmentNotice.vue'
import { TASK_STATUS, TASK_TYPE_OPTIONS, getTask, saveTaskDraft, submitTaskForPublish } from '../mock/tasks.js'

const route = useRoute()
const router = useRouter()
const currentAdvisor = { id: 'T001', name: '张明' }
const existing = route.params.id ? getTask(route.params.id) : null
const editable = !route.params.id || Boolean(existing && [TASK_STATUS.DRAFT, TASK_STATUS.PUBLISH_REJECTED].includes(existing.status))
const form = reactive({
  taskId: existing?.taskId || '', title: existing?.title || '', taskType: existing?.taskType || '',
  description: existing?.description || '', resultRequirement: existing?.resultRequirement || '',
  registrationDeadline: (existing?.registrationDeadline || '').replace(' ', 'T'),
  attachments: (existing?.attachments || []).map((file) => ({ ...file })),
})
const feedback = ref('')
const pageTitle = computed(() => existing ? '编辑发布任务' : '发布新任务')
function nowText() { return new Date().toLocaleString('zh-CN', { hour12: false }).replaceAll('/', '-') }
function selectAttachments(event) { Array.from(event.target.files || []).forEach((file, index) => form.attachments.push({ id: `TASK-ATT-${Date.now()}-${index}`, name: file.name, type: file.type || '未知类型', size: `${file.size} B`, uploadedAt: nowText(), mockUrl: URL.createObjectURL(file) })); event.target.value = '' }
function removeAttachment(id) { const file = form.attachments.find((item) => item.id === id); if (file?.mockUrl?.startsWith('blob:')) URL.revokeObjectURL(file.mockUrl); form.attachments = form.attachments.filter((item) => item.id !== id) }
function payload() { return { taskId: form.taskId, title: form.title.trim(), taskType: form.taskType, description: form.description.trim(), resultRequirement: form.resultRequirement.trim(), registrationDeadline: form.registrationDeadline.replace('T', ' '), attachments: form.attachments.map((file) => ({ ...file })), advisorId: currentAdvisor.id, advisorName: currentAdvisor.name, source: 'advisor' } }
function validate() { if (!form.title.trim()) return '任务名称必填。'; if (!form.taskType) return '任务类型必填。'; if (!form.description.trim()) return '任务说明必填。'; if (!form.resultRequirement.trim()) return '成果提交要求必填。'; if (!form.registrationDeadline) return '报名截止时间必填。'; if (new Date(form.registrationDeadline).getTime() <= Date.now()) return '报名截止时间必须晚于当前时间。'; return '' }
function save() { if (!editable) return; const task = saveTaskDraft(payload()); if (!task) return window.alert('当前状态不可保存草稿。'); window.alert('草稿保存成功。'); router.push('/teacher/publish-task') }
function submit() { if (!editable) return; const error = validate(); if (error) { feedback.value = error; return window.alert(error) } const task = submitTaskForPublish(payload()); if (!task) return window.alert('当前状态不可提交发布申请。'); window.alert('发布申请已提交，等待管理员确认。'); router.push('/teacher/publish-task') }
</script>

<template><main class="page"><div class="content"><header><p class="eyebrow">T202 · PUBLISH TASK</p><h1>{{ pageTitle }}</h1><p>任务发布不预设课时，课时由队长提交成果时申请。</p></header><p v-if="!editable" class="notice">当前任务状态不可编辑。</p><form @submit.prevent="submit"><section class="card"><h2>任务基本信息</h2><div class="grid"><label><span>任务名称 *</span><input v-model="form.title" :disabled="!editable" /></label><label><span>任务类型 *</span><select v-model="form.taskType" :disabled="!editable"><option value="">请选择</option><option v-for="option in TASK_TYPE_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option></select></label><label><span>报名截止时间 *</span><input v-model="form.registrationDeadline" :disabled="!editable" type="datetime-local" /></label><label class="wide"><span>任务说明 *</span><textarea v-model="form.description" :disabled="!editable" rows="5" /></label><label class="wide"><span>成果提交要求 *</span><textarea v-model="form.resultRequirement" :disabled="!editable" rows="5" /></label></div></section><section class="card"><h2>附件上传</h2><AttachmentNotice title="任务附件上传说明" description="当前页面保留 Mock 上传；正式接入时先上传附件再提交 attachment_ids。" :required="false" :accept-types="['PDF','Word','Excel','PPT','图片','压缩包']" /><input type="file" multiple :disabled="!editable" @change="selectAttachments" /><article v-for="file in form.attachments" :key="file.id" class="file"><span>{{ file.name }}</span><button type="button" @click="removeAttachment(file.id)">删除</button></article></section><p v-if="feedback" class="notice">{{ feedback }}</p><div class="actions"><button type="button" @click="router.push('/teacher/publish-task')">返回</button><button type="button" :disabled="!editable" @click="save">保存草稿</button><button class="primary" type="submit" :disabled="!editable">提交发布申请</button></div></form></div></main></template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,980px);margin:auto}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.card{margin:20px 0;padding:24px;border:1px solid #e2e8f0;border-radius:15px;background:#fff}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.wide{grid-column:1/-1}label span{display:block;margin-bottom:8px;font-weight:700}input,select,textarea{box-sizing:border-box;width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:9px;font:inherit}.file{display:flex;justify-content:space-between;margin-top:10px;padding:12px;background:#f8fafc}.notice{padding:12px;color:#b91c1c;background:#fef2f2}.actions{display:flex;justify-content:flex-end;gap:10px}.actions button,.file button{padding:9px 15px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font-weight:700}.actions .primary{color:#fff;background:#2563eb}@media(max-width:650px){.grid{grid-template-columns:1fr}.wide{grid-column:auto}}</style>
