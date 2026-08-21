<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { submitComplaint } from '../api/complaintApi.js'
import { uploadAttachment } from '../api/fileApi.js'

const router = useRouter()
const MAX_ATTACHMENTS = 10
const categoryOptions = [
  { value: 'personnel_behavior', label: '人员行为' },
  { value: 'service_quality', label: '服务质量' },
  { value: 'process_violation', label: '流程违规' },
  { value: 'other', label: '其他问题' },
]
const form = reactive({ category: '', content: '', files: [], attachmentIds: [] })

async function selectFiles(event) {
  const selectedFiles = Array.from(event.target.files || [])
  const remainingCount = MAX_ATTACHMENTS - form.attachmentIds.length
  if (selectedFiles.length > remainingCount) {
    window.alert(`投诉附件最多上传 ${MAX_ATTACHMENTS} 个。`)
  }
  for (const file of selectedFiles.slice(0, remainingCount)) {
    try {
      const uploaded = await uploadAttachment(file, 'complaint')
      form.files.push({ ...uploaded.attachment, id: uploaded.id, name: file.name })
      form.attachmentIds.push(uploaded.id)
    } catch (error) { window.alert(error?.message || '投诉附件上传失败') }
  }
  event.target.value = ''
}

function removeFile(id) {
  form.files = form.files.filter((item) => item.id !== id)
  form.attachmentIds = form.attachmentIds.filter((item) => item !== id)
}

async function submit() {
  const content = form.content.trim()
  if (!form.category) return window.alert('请选择投诉分类。')
  if (content.length < 10 || content.length > 5000) return window.alert('投诉内容去除首尾空白后须为 10～5000 个字符。')
  if (form.attachmentIds.length > MAX_ATTACHMENTS) return window.alert(`投诉附件最多上传 ${MAX_ATTACHMENTS} 个。`)
  try {
    const complaint = await submitComplaint({
      category: form.category,
      content,
      attachment_ids: form.attachmentIds,
    })
    const { id, complaint_no: complaintNo } = complaint
    await router.push({
      path: `/student/complaints/submitted/${id}`,
      query: { status: complaint.status || 'submitted', complaint_no: complaintNo },
    })
  } catch (error) { window.alert(error?.message || '投诉提交失败') }
}
</script>

<template><main class="page"><div class="content">
  <header><div><p class="eyebrow">S801 · COMPLAINT</p><h1>发起问题反馈与投诉</h1><p>选择投诉分类，填写投诉内容并按需上传附件。</p></div><RouterLink to="/student/feedback">返回问题反馈</RouterLink></header>
  <section class="card"><h2>投诉分类</h2><select v-model="form.category"><option value="" disabled>请选择投诉分类</option><option v-for="option in categoryOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></section>
  <section class="card"><h2>投诉内容</h2><textarea v-model="form.content" rows="7" placeholder="请详细说明需要反馈的问题"></textarea></section>
  <section class="card"><h2>投诉材料（可选，最多 10 个）</h2><input type="file" multiple :disabled="form.attachmentIds.length >= MAX_ATTACHMENTS" @change="selectFiles" /><article v-for="file in form.files" :key="file.id" class="file"><span>{{ file.name }}</span><button type="button" @click="removeFile(file.id)">删除</button></article></section>
  <div class="actions"><RouterLink to="/student/feedback">返回</RouterLink><button type="button" @click="submit">提交问题反馈与投诉</button></div>
</div></main></template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,900px);margin:auto}header{display:flex;justify-content:space-between}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.card{margin:18px 0;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}textarea,input,select{box-sizing:border-box;width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:9px}.file{display:flex;justify-content:space-between;margin-top:10px;padding:12px;background:#f8fafc}.actions{display:flex;justify-content:flex-end;gap:10px}.actions a,.actions button,.file button{padding:9px 15px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;text-decoration:none}.actions>button{color:#fff;background:#2563eb}</style>
