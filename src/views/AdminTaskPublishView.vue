<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ADMIN_TASK_ADVISORS, TASK_TYPE_OPTIONS } from '../mock/tasks.js'
import { downloadAttachment, getAttachmentErrorMessage, previewAttachment, uploadAttachment } from '../api/fileApi.js'
import { getAdminTask, getAdminTasks, publishAdminTask, saveAdminTaskDraft } from '../api/taskApi.js'
import { adaptTaskEnvelope, adaptTaskList, toTaskPayload } from '../adapters/taskAdapter.js'
import { loadAdvisorOptions, loadTaskTypeOptions } from '../services/commonDependencyService.js'
import { getServerNowMs, systemTimeState } from '../services/systemTimeService.js'
import { toShanghaiDateTimeInput, toShanghaiIso } from '../utils/taskDateTime.js'

const router = useRouter()
const submitting = ref(false)
const saving = ref(false)
const draftId = ref(null)
const DRAFT_STORAGE_KEY = 'admin-task-publish-draft-id'
const taskTypeOptions = ref(TASK_TYPE_OPTIONS.map((item) => ({ ...item })))
const advisorOptions = ref(ADMIN_TASK_ADVISORS.map((item) => ({ ...item })))
const form = reactive({
  title: '', taskType: '', description: '', resultRequirement: '', advisorId: '',
  registrationDeadline: '', attachments: [],
})
const advisor = computed(() => advisorOptions.value.find((item) => item.advisorId === form.advisorId))
const formatSize = (size) => size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))} KB` : `${(size / 1024 / 1024).toFixed(2)} MB`

async function chooseFiles(event) {
  const files = Array.from(event.target.files || [])
  event.target.value = ''
  for (const file of files) {
    try {
      const result = await uploadAttachment(file, 'task')
      form.attachments.push({ ...result.attachment, fileName: result.attachment.name, fileType: result.attachment.type, fileSize: formatSize(result.attachment.size), uploadTime: result.attachment.uploadedAt, attachmentIds: result.attachmentIds })
    } catch (error) {
      console.error('[attachment] 管理员任务附件上传失败。', error)
      window.alert('任务附件上传失败，请重试。')
    }
  }
}
function removeFile(index) {
  form.attachments.splice(index, 1)
}
async function preview(file) { try { await previewAttachment(file) } catch (error) { window.alert(getAttachmentErrorMessage(error, '附件预览失败，请稍后重试。')) } }
async function download(file) { try { await downloadAttachment(file) } catch (error) { window.alert(getAttachmentErrorMessage(error, '附件下载失败，请稍后重试。')) } }

function validateForm() {
  if (!form.title.trim() || !form.taskType || !form.description.trim() || !form.resultRequirement.trim() || !advisor.value || !form.registrationDeadline) {
    return '请完整填写任务名称、类型、说明、成果要求、指导老师和报名截止时间。'
  }
  return ''
}

function buildPayload() {
  return toTaskPayload({
    ...form,
    title: form.title.trim(),
    description: form.description.trim(),
    resultRequirement: form.resultRequirement.trim(),
    taskTypeId: Number(form.taskType),
    advisorId: Number(form.advisorId),
    registrationDeadline: toShanghaiIso(form.registrationDeadline),
    attachmentIds: form.attachments.flatMap((item) => item.attachmentIds || (Number.isInteger(item.id) ? [item.id] : [])),
  })
}

function storeDraftId(id) {
  draftId.value = id
  try { window.localStorage.setItem(DRAFT_STORAGE_KEY, String(id)) } catch { /* storage may be unavailable */ }
}

function getStoredDraftId() {
  try {
    const id = Number(window.localStorage.getItem(DRAFT_STORAGE_KEY))
    return Number.isInteger(id) && id > 0 ? id : null
  } catch {
    return null
  }
}

function restoreDraft(payload) {
  const task = adaptTaskEnvelope(payload)
  if (!task || task.status !== 'draft') return false
  const id = Number(task.id)
  if (!Number.isInteger(id) || id <= 0) return false
  form.title = task.title ?? ''
  form.taskType = task.taskTypeId ?? ''
  form.description = task.description ?? ''
  form.resultRequirement = task.resultRequirement ?? ''
  form.advisorId = task.advisorId ?? ''
  form.registrationDeadline = toShanghaiDateTimeInput(task.registrationDeadline)
  form.attachments = (task.attachments ?? []).map((attachment) => ({
    ...attachment,
    fileName: attachment.name,
    fileType: attachment.type,
    fileSize: formatSize(Number(attachment.size) || 0),
    uploadTime: attachment.uploadedAt,
    attachmentIds: [Number(attachment.id)].filter((attachmentId) => Number.isInteger(attachmentId) && attachmentId > 0),
  }))
  storeDraftId(id)
  return true
}

async function loadExistingDraft() {
  const storedId = getStoredDraftId()
  if (storedId) {
    try {
      if (restoreDraft(await getAdminTask(storedId))) return
    } catch { /* fall through to the server-side draft list */ }
  }
  const drafts = adaptTaskList(await getAdminTasks({ status: 'draft', page: 1, page_size: 100 }))
    .filter((task) => task.status === 'draft')
    .sort((left, right) => Number(right.id) - Number(left.id))
  if (!drafts[0]?.id) return
  if (restoreDraft(await getAdminTask(drafts[0].id))) window.alert('已加载上次保存的任务草稿。')
}

async function saveDraft() {
  const error = validateForm()
  if (error) return window.alert(error)
  saving.value = true
  try {
    const result = await saveAdminTaskDraft(buildPayload())
    const task = result?.task ?? result
    const id = Number(task?.id ?? result?.id)
    const status = task?.status ?? result?.status
    if (!Number.isInteger(id) || id <= 0) throw new Error('后端未返回有效的草稿任务 ID')
    if (status !== 'draft') throw new Error(`草稿状态异常：${status ?? '未返回状态'}`)
    storeDraftId(id)
    window.alert(`任务草稿保存成功（ID：${id}）。`)
  } catch (error) {
    window.alert(error.message || '任务草稿保存失败。')
  } finally {
    saving.value = false
  }
}

async function submit() {
  const error = validateForm()
  if (error) return window.alert(error)
  const deadline = Date.parse(toShanghaiIso(form.registrationDeadline))
  if (systemTimeState.initialized && deadline <= getServerNowMs()) return window.alert('报名截止时间必须晚于服务器当前时间。')
  submitting.value = true
  try {
    const task = await publishAdminTask(buildPayload())
    window.alert('任务已直接发布，学生端任务广场可见。')
    router.push(`/admin/tasks/list/${task.id}`)
  } catch (error) { window.alert(error.message || '任务发布失败。') }
  finally { submitting.value = false }
}
onMounted(async () => {
  const [types, advisors] = await Promise.all([loadTaskTypeOptions(TASK_TYPE_OPTIONS), loadAdvisorOptions(ADMIN_TASK_ADVISORS)])
  taskTypeOptions.value = types.filter((item) => item.allowAdminTask !== false)
  advisorOptions.value = advisors
  try { await loadExistingDraft() } catch (error) { window.alert(error.message || '任务草稿加载失败。') }
})
</script>

<template>
  <main class="page"><div class="content">
    <header><div><p class="breadcrumb">管理端 / 任务管理 / 发布任务</p><p class="eyebrow">ADMIN DIRECT PUBLISH</p><h1>管理员直接发布任务</h1><p>任务提交后直接发布到学生端任务广场，不进入管理员二次确认。</p></div><RouterLink class="back" to="/admin/tasks">返回任务管理</RouterLink></header>
    <form class="panel" @submit.prevent="submit">
      <h2>任务信息</h2><div class="grid">
        <label><span>任务名称 *</span><input v-model="form.title" /></label>
        <label><span>任务类型 *</span><select v-model="form.taskType"><option value="">请选择</option><option v-for="item in taskTypeOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
        <label><span>指导老师 *</span><select v-model="form.advisorId"><option value="">请选择</option><option v-for="item in advisorOptions" :key="item.advisorId" :value="item.advisorId">{{ item.advisorName }}（{{ item.college || item.major || '未设置院系' }}）</option></select></label>
        <label class="wide"><span>任务说明 *</span><textarea v-model="form.description" rows="4" /></label>
        <label class="wide"><span>成果提交要求 *</span><textarea v-model="form.resultRequirement" rows="3" /></label>
        <label><span>报名截止时间 *</span><input v-model="form.registrationDeadline" type="datetime-local" /></label>
      </div>
      <section class="upload"><h2>附件上传</h2><p>附件上传后端并保存 attachment_ids。</p><label class="file-button">选择本地文件<input type="file" multiple @change="chooseFiles" /></label>
        <div v-if="form.attachments.length" class="table-wrap"><table><thead><tr><th>文件名</th><th>类型</th><th>大小</th><th>上传时间</th><th>操作</th></tr></thead><tbody><tr v-for="(file,index) in form.attachments" :key="file.id"><td>{{ file.fileName }}</td><td>{{ file.fileType }}</td><td>{{ file.fileSize }}</td><td>{{ file.uploadTime }}</td><td><button type="button" class="link" @click="preview(file)">预览</button><button type="button" class="link" @click="download(file)">下载</button><button type="button" class="danger" @click="removeFile(index)">删除</button></td></tr></tbody></table></div><p v-else class="empty">暂未选择附件</p>
      </section>
      <div class="actions"><RouterLink class="cancel" to="/admin/tasks">返回</RouterLink><button class="cancel" type="button" :disabled="saving || submitting" @click="saveDraft">{{ saving ? '保存中…' : '保存草稿' }}</button><button class="submit" type="submit" :disabled="submitting || saving">{{ submitting ? '发布中…' : '直接发布' }}</button></div>
    </form>
  </div></main>
</template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1100px);margin:auto}header{display:flex;justify-content:space-between;gap:20px;margin-bottom:22px}h1{margin:0 0 8px}.breadcrumb{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800}.back,.cancel{height:max-content;padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;color:#2563eb;background:#fff;font-weight:700;text-decoration:none}.panel{padding:24px;border:1px solid #e2e8f0;border-radius:16px;background:#fff}.panel h2{margin:0 0 16px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.wide{grid-column:1/-1}label span{display:block;margin-bottom:7px;font-weight:700}input,select,textarea{box-sizing:border-box;width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}textarea{resize:vertical}.upload{margin-top:28px;padding-top:24px;border-top:1px solid #e2e8f0}.upload>p{color:#64748b}.file-button{display:inline-block;padding:10px 16px;border-radius:9px;color:#fff;background:#2563eb;font-weight:700;cursor:pointer}.file-button input{display:none}.table-wrap{margin-top:16px;overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left}th{background:#f8fafc}.link,.danger{border:0;background:none;font-weight:700;cursor:pointer}.link{color:#2563eb}.danger{color:#dc2626}.empty{padding:18px;text-align:center}.actions{display:flex;justify-content:flex-end;gap:12px;margin-top:28px}.submit{padding:10px 20px;border:0;border-radius:9px;color:#fff;background:#2563eb;font:inherit;font-weight:700;cursor:pointer}.submit:disabled{opacity:.6}@media(max-width:700px){.page{padding:24px 14px}header{flex-direction:column}.grid{grid-template-columns:1fr}.wide{grid-column:auto}}
</style>
