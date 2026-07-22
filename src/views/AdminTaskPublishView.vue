<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ADMIN_TASK_ADVISORS, TASK_TYPE_OPTIONS, adminDirectPublishTask } from '../mock/tasks.js'

const router = useRouter()
const submitting = ref(false)
const form = reactive({
  title: '', taskType: '', description: '', requirement: '', resultRequirement: '', category: '', advisorId: '',
  registrationStartTime: '', registrationDeadline: '', resultDeadline: '', hours: '', maxParticipants: '', attachments: [],
})
const advisor = computed(() => ADMIN_TASK_ADVISORS.find((item) => item.advisorId === form.advisorId))
const formatSize = (size) => size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))} KB` : `${(size / 1024 / 1024).toFixed(2)} MB`
const formatTime = (date = new Date()) => date.toLocaleString('zh-CN', { hour12: false }).replaceAll('/', '-')

function chooseFiles(event) {
  Array.from(event.target.files || []).forEach((file) => form.attachments.push({
    id: `file_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    fileName: file.name,
    fileType: file.type || file.name.split('.').pop()?.toLowerCase() || 'unknown',
    fileSize: formatSize(file.size),
    uploadTime: formatTime(),
    mockUrl: URL.createObjectURL(file),
  }))
  event.target.value = ''
}
function removeFile(index) {
  const [file] = form.attachments.splice(index, 1)
  if (file?.mockUrl) URL.revokeObjectURL(file.mockUrl)
}
function preview(file) {
  if (file.mockUrl) window.open(file.mockUrl, '_blank')
  else window.alert('当前为 Mock 附件预览，真实预览需后端文件服务支持。')
}
function download() { window.alert('当前为 Mock 附件下载，真实下载需后端文件服务支持。') }
function submit() {
  if (!form.title.trim() || !form.taskType || !form.description.trim() || !form.requirement.trim() || !form.resultRequirement.trim() || !form.category.trim() || !advisor.value || !form.registrationStartTime || !form.registrationDeadline || !form.resultDeadline) return window.alert('请完整填写任务名称、类型、说明、要求、类别、指导老师和各项时间。')
  const start = new Date(form.registrationStartTime).getTime(); const deadline = new Date(form.registrationDeadline).getTime(); const resultDeadline = new Date(form.resultDeadline).getTime()
  if (deadline <= start) return window.alert('报名截止时间必须晚于报名开始时间。')
  if (deadline <= Date.now()) return window.alert('报名截止时间必须晚于当前时间。')
  if (resultDeadline <= deadline) return window.alert('成果提交截止时间必须晚于报名截止时间。')
  if (Number(form.hours) <= 0 || Number(form.maxParticipants) <= 0) return window.alert('任务课时数和人数限制必须大于 0。')
  submitting.value = true
  try {
    const task = adminDirectPublishTask({ ...form, advisorName: advisor.value.advisorName, attachments: form.attachments.map((item) => ({ ...item })) })
    window.alert('任务已直接发布，学生端任务广场可见。')
    router.push(`/admin/tasks/list/${task.taskId}`)
  } catch (error) { window.alert(error.message || '任务发布失败。') }
  finally { submitting.value = false }
}
</script>

<template>
  <main class="page"><div class="content">
    <header><div><p class="breadcrumb">管理端 / 任务管理 / 发布任务</p><p class="eyebrow">ADMIN DIRECT PUBLISH</p><h1>管理员直接发布任务</h1><p>任务提交后直接发布到学生端任务广场，不进入管理员二次确认。</p></div><RouterLink class="back" to="/admin/tasks">返回任务管理</RouterLink></header>
    <form class="panel" @submit.prevent="submit">
      <h2>任务信息</h2><div class="grid">
        <label><span>任务名称 *</span><input v-model="form.title" /></label>
        <label><span>任务类型 *</span><select v-model="form.taskType"><option value="">请选择</option><option v-for="item in TASK_TYPE_OPTIONS" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
        <label><span>所属课程或项目类别 *</span><input v-model="form.category" placeholder="例如：创新实践" /></label>
        <label><span>指导老师 *</span><select v-model="form.advisorId"><option value="">请选择</option><option v-for="item in ADMIN_TASK_ADVISORS" :key="item.advisorId" :value="item.advisorId">{{ item.advisorName }}（{{ item.college }}）</option></select></label>
        <label class="wide"><span>任务说明 *</span><textarea v-model="form.description" rows="4" /></label>
        <label class="wide"><span>任务要求 *</span><textarea v-model="form.requirement" rows="3" /></label>
        <label class="wide"><span>成果提交要求 *</span><textarea v-model="form.resultRequirement" rows="3" /></label>
        <label><span>报名开始时间 *</span><input v-model="form.registrationStartTime" type="datetime-local" /></label>
        <label><span>报名截止时间 *</span><input v-model="form.registrationDeadline" type="datetime-local" /></label>
        <label><span>成果提交截止时间 *</span><input v-model="form.resultDeadline" type="datetime-local" /></label>
        <label><span>任务课时数 *</span><input v-model="form.hours" type="number" min="0.5" step="0.5" /></label>
        <label><span>人数限制 *</span><input v-model="form.maxParticipants" type="number" min="1" step="1" /></label>
      </div>
      <section class="upload"><h2>附件上传</h2><p>请从本地选择任务说明、成果要求、模板文件或其他辅助材料。当前阶段为 Mock 上传，仅保存文件信息，不会真正上传到服务器。</p><label class="file-button">选择本地文件<input type="file" multiple @change="chooseFiles" /></label>
        <div v-if="form.attachments.length" class="table-wrap"><table><thead><tr><th>文件名</th><th>类型</th><th>大小</th><th>上传时间</th><th>操作</th></tr></thead><tbody><tr v-for="(file,index) in form.attachments" :key="file.id"><td>{{ file.fileName }}</td><td>{{ file.fileType }}</td><td>{{ file.fileSize }}</td><td>{{ file.uploadTime }}</td><td><button type="button" class="link" @click="preview(file)">预览</button><button type="button" class="link" @click="download">下载</button><button type="button" class="danger" @click="removeFile(index)">删除</button></td></tr></tbody></table></div><p v-else class="empty">暂未选择附件</p>
      </section>
      <div class="actions"><RouterLink class="cancel" to="/admin/tasks">返回</RouterLink><button class="submit" type="submit" :disabled="submitting">{{ submitting ? '发布中…' : '直接发布' }}</button></div>
    </form>
  </div></main>
</template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1100px);margin:auto}header{display:flex;justify-content:space-between;gap:20px;margin-bottom:22px}h1{margin:0 0 8px}.breadcrumb{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800}.back,.cancel{height:max-content;padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;color:#2563eb;background:#fff;font-weight:700;text-decoration:none}.panel{padding:24px;border:1px solid #e2e8f0;border-radius:16px;background:#fff}.panel h2{margin:0 0 16px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.wide{grid-column:1/-1}label span{display:block;margin-bottom:7px;font-weight:700}input,select,textarea{box-sizing:border-box;width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}textarea{resize:vertical}.upload{margin-top:28px;padding-top:24px;border-top:1px solid #e2e8f0}.upload>p{color:#64748b}.file-button{display:inline-block;padding:10px 16px;border-radius:9px;color:#fff;background:#2563eb;font-weight:700;cursor:pointer}.file-button input{display:none}.table-wrap{margin-top:16px;overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left}th{background:#f8fafc}.link,.danger{border:0;background:none;font-weight:700;cursor:pointer}.link{color:#2563eb}.danger{color:#dc2626}.empty{padding:18px;text-align:center}.actions{display:flex;justify-content:flex-end;gap:12px;margin-top:28px}.submit{padding:10px 20px;border:0;border-radius:9px;color:#fff;background:#2563eb;font:inherit;font-weight:700;cursor:pointer}.submit:disabled{opacity:.6}@media(max-width:700px){.page{padding:24px 14px}header{flex-direction:column}.grid{grid-template-columns:1fr}.wide{grid-column:auto}}
</style>
