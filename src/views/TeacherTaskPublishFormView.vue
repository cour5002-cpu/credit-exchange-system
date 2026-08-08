<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AttachmentNotice from '../components/AttachmentNotice.vue'
import { TASK_TYPE_OPTIONS } from '../mock/tasks.js'
import { getAdvisorTask, getAdvisorTasks, publishAdvisorTask, saveAdvisorTaskDraft } from '../api/taskApi.js'
import { adaptTaskEnvelope, adaptTaskList, toAdvisorTaskPayload } from '../adapters/taskAdapter.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'
import { downloadAttachment, getAttachmentErrorMessage, previewAttachment, uploadAttachment } from '../api/fileApi.js'
import { loadTaskTypeOptions } from '../services/commonDependencyService.js'
import { getServerNowMs, systemTimeState } from '../services/systemTimeService.js'
import { toShanghaiDateTimeInput, toShanghaiIso } from '../utils/taskDateTime.js'

const route = useRoute()
const router = useRouter()
const currentAdvisor = { id: 'T001', name: '张明' }
const existing = null
const editable = !route.params.id
const form = reactive({
  taskId: existing?.taskId || '', title: existing?.title || '', taskType: existing?.taskType || '',
  description: existing?.description || '', resultRequirement: existing?.resultRequirement || '',
  registrationDeadline: toShanghaiDateTimeInput(existing?.registrationDeadline),
  attachments: (existing?.attachments || []).map((file) => ({ ...file })),
})
const feedback = ref('')
const draftId = ref(null)
const DRAFT_STORAGE_KEY = `advisor-task-publish-draft-id:${currentAdvisor.id}`
const taskTypeOptions = ref(TASK_TYPE_OPTIONS.map((item) => ({ ...item })))
const pageTitle = computed(() => existing ? '编辑发布任务' : '发布新任务')
async function selectAttachments(event) { const files = Array.from(event.target.files || []); event.target.value = ''; for (const file of files) { try { const result = await uploadAttachment(file, 'task'); form.attachments.push({ ...result.attachment, attachmentIds: result.attachmentIds }) } catch (error) { console.error('[attachment] 任务附件上传失败。', error); window.alert('任务附件上传失败，请重新上传。') } } }
function removeAttachment(id) { form.attachments = form.attachments.filter((item) => item.id !== id) }
async function previewFile(file){try{await previewAttachment(file)}catch(error){window.alert(getAttachmentErrorMessage(error,'附件预览失败，请稍后重试。'))}}async function downloadFile(file){try{await downloadAttachment(file)}catch(error){window.alert(getAttachmentErrorMessage(error,'附件下载失败，请稍后重试。'))}}
function payload() { return { taskId: form.taskId, title: form.title.trim(), taskType: form.taskType, description: form.description.trim(), resultRequirement: form.resultRequirement.trim(), registrationDeadline: toShanghaiIso(form.registrationDeadline), attachments: form.attachments.map((file) => ({ ...file })), attachmentIds: form.attachments.flatMap((file) => file.attachmentIds || (Number.isInteger(file.id) ? [file.id] : [])), advisorId: currentAdvisor.id, advisorName: currentAdvisor.name, source: 'advisor' } }
function validate() { if (!form.title.trim()) return '任务名称必填。'; if (!form.taskType) return '任务类型必填。'; if (!form.description.trim()) return '任务说明必填。'; if (!form.resultRequirement.trim()) return '成果提交要求必填。'; if (!form.registrationDeadline) return '报名截止时间必填。'; if (systemTimeState.initialized&&Date.parse(toShanghaiIso(form.registrationDeadline))<=getServerNowMs()) return '报名截止时间必须晚于服务器当前时间。'; return '' }
function buildPayload() { const source=payload();return toAdvisorTaskPayload({title:source.title,description:source.description,taskTypeId:source.taskType,resultRequirement:source.resultRequirement,registrationDeadline:source.registrationDeadline,attachmentIds:source.attachmentIds}) }
function storeDraftId(id) { draftId.value=id;try{window.localStorage.setItem(DRAFT_STORAGE_KEY,String(id))}catch{/* storage may be unavailable */} }
function getStoredDraftId() { try { const id=Number(window.localStorage.getItem(DRAFT_STORAGE_KEY));return Number.isInteger(id)&&id>0?id:null } catch { return null } }
function restoreDraft(response) { const task=adaptTaskEnvelope(response);if(!task||task.status!=='draft')return false;const id=Number(task.id);if(!Number.isInteger(id)||id<=0)return false;form.taskId=id;form.title=task.title??'';form.taskType=task.taskTypeId??'';form.description=task.description??'';form.resultRequirement=task.resultRequirement??'';form.registrationDeadline=toShanghaiDateTimeInput(task.registrationDeadline);form.attachments=(task.attachments??[]).map((file)=>({...file,attachmentIds:[Number(file.id)].filter((attachmentId)=>Number.isInteger(attachmentId)&&attachmentId>0)}));storeDraftId(id);return true }
async function loadExistingDraft() { const storedId=getStoredDraftId();if(storedId){try{if(restoreDraft(await getAdvisorTask(storedId)))return}catch{/* fall through to server list */}}const drafts=adaptTaskList(await getAdvisorTasks({status:'draft',page:1,page_size:100})).filter((task)=>task.status==='draft').sort((left,right)=>Number(right.id)-Number(left.id));if(drafts[0]?.id&&restoreDraft(await getAdvisorTask(drafts[0].id)))feedback.value='已加载上次保存的任务草稿。' }
async function save() { if (!editable) return; const error=validate();if(error)return window.alert(error);try{const response=await saveAdvisorTaskDraft(buildPayload());const task=response?.task??response;const id=Number(task?.id??response?.id);const status=task?.status??response?.status;if(!Number.isInteger(id)||id<=0)throw new Error('后端未返回有效的草稿任务 ID');if(status!=='draft')throw new Error(`草稿状态异常：${status??'未返回状态'}`);storeDraftId(id);feedback.value=`任务草稿保存成功（ID：${id}）。`;window.alert(feedback.value)}catch(error){window.alert(getApiErrorMessage(error,'草稿保存失败'))} }
async function submit() { if (!editable) return; const error = validate(); if (error) { feedback.value = error; return window.alert(error) } try{await publishAdvisorTask(buildPayload());window.alert('发布申请已提交，等待管理员确认。');router.push('/teacher/publish-task')}catch(apiError){window.alert(getApiErrorMessage(apiError,'发布申请提交失败'))} }
onMounted(async () => { taskTypeOptions.value = (await loadTaskTypeOptions(TASK_TYPE_OPTIONS)).filter((item) => item.allowTeacherTask !== false);if(!route.params.id){try{await loadExistingDraft()}catch(error){feedback.value=getApiErrorMessage(error,'草稿加载失败')}} })
</script>

<template><main class="page"><div class="content"><header><p class="eyebrow">T202 · PUBLISH TASK</p><h1>{{ pageTitle }}</h1><p>任务发布不预设课时，课时由队长提交成果时申请。</p></header><p v-if="!editable" class="notice">当前任务状态不可编辑。</p><form @submit.prevent="submit"><section class="card"><h2>任务基本信息</h2><div class="grid"><label><span>任务名称 *</span><input v-model="form.title" :disabled="!editable" /></label><label><span>任务类型 *</span><select v-model="form.taskType" :disabled="!editable"><option value="">请选择</option><option v-for="option in taskTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label><label><span>报名截止时间 *</span><input v-model="form.registrationDeadline" :disabled="!editable" type="datetime-local" /></label><label class="wide"><span>任务说明 *</span><textarea v-model="form.description" :disabled="!editable" rows="5" /></label><label class="wide"><span>成果提交要求 *</span><textarea v-model="form.resultRequirement" :disabled="!editable" rows="5" /></label></div></section><section class="card"><h2>附件上传</h2><AttachmentNotice title="任务附件上传说明" description="附件上传后端并保存 attachment_ids。" :required="false" :accept-types="['PDF','Word','Excel','PPT','图片','压缩包']" /><input type="file" multiple :disabled="!editable" @change="selectAttachments" /><article v-for="file in form.attachments" :key="file.id" class="file"><span>{{ file.name }}</span><span><button type="button" @click="previewFile(file)">预览</button><button type="button" @click="downloadFile(file)">下载</button><button type="button" @click="removeAttachment(file.id)">删除</button></span></article></section><p v-if="feedback" class="notice">{{ feedback }}</p><div class="actions"><button type="button" @click="router.push('/teacher/publish-task')">返回</button><button type="button" :disabled="!editable" @click="save">保存草稿</button><button class="primary" type="submit" :disabled="!editable">提交发布申请</button></div></form></div></main></template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,980px);margin:auto}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.card{margin:20px 0;padding:24px;border:1px solid #e2e8f0;border-radius:15px;background:#fff}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.wide{grid-column:1/-1}label span{display:block;margin-bottom:8px;font-weight:700}input,select,textarea{box-sizing:border-box;width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:9px;font:inherit}.file{display:flex;justify-content:space-between;margin-top:10px;padding:12px;background:#f8fafc}.notice{padding:12px;color:#b91c1c;background:#fef2f2}.actions{display:flex;justify-content:flex-end;gap:10px}.actions button,.file button{padding:9px 15px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font-weight:700}.actions .primary{color:#fff;background:#2563eb}@media(max-width:650px){.grid{grid-template-columns:1fr}.wide{grid-column:auto}}</style>
