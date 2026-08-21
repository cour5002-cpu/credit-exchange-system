<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getStudentComplaint } from '../api/complaintApi.js'
import { adaptComplaintEnvelope } from '../adapters/complaintAdapter.js'
import { downloadAttachment, getAttachmentErrorMessage, previewAttachment } from '../api/fileApi.js'

const route = useRoute()
const complaint = ref(null)
const loading = ref(true)
const errorMessage = ref('')

function getErrorMessage(error) {
  const status = Number(error?.status ?? error?.response?.status)
  if (status === 403) return '无权限查看该投诉。'
  if (status === 404) return '投诉不存在。'
  return error?.message || '投诉详情加载失败，请稍后重试。'
}

async function loadComplaint() {
  loading.value = true
  complaint.value = null
  errorMessage.value = ''
  try {
    complaint.value = adaptComplaintEnvelope(await getStudentComplaint(route.params.id))
    if (!complaint.value) errorMessage.value = '投诉不存在。'
  } catch (error) {
    complaint.value = null
    errorMessage.value = getErrorMessage(error)
  } finally {
    loading.value = false
  }
}

async function preview(file) {
  try { await previewAttachment(file) }
  catch (error) { window.alert(getAttachmentErrorMessage(error, 'preview')) }
}

async function download(file) {
  try { await downloadAttachment(file) }
  catch (error) { window.alert(getAttachmentErrorMessage(error, 'download')) }
}

onMounted(loadComplaint)
</script>

<template>
  <main class="page"><div class="content">
    <p v-if="loading" class="state">投诉详情加载中...</p>
    <section v-else-if="errorMessage" class="state error" role="alert"><p>{{ errorMessage }}</p><RouterLink to="/student/complaints">返回投诉记录</RouterLink></section>
    <template v-else-if="complaint">
      <header><div><p class="eyebrow">COMPLAINT DETAIL</p><h1>{{ complaint.complaintNo || `投诉 #${complaint.id}` }}</h1></div><span class="status">{{ complaint.statusText }}</span></header>
      <section class="card"><h2>投诉信息</h2><dl><div><dt>投诉分类</dt><dd>{{ complaint.categoryText }}</dd></div><div><dt>提交时间</dt><dd>{{ complaint.submittedAt || complaint.createdAt || '--' }}</dd></div><div><dt>开始处理时间</dt><dd>{{ complaint.processingStartedAt || '--' }}</dd></div><div><dt>处理完成时间</dt><dd>{{ complaint.resolvedAt || '--' }}</dd></div></dl></section>
      <section class="card"><h2>投诉内容</h2><p class="plain-text">{{ complaint.content }}</p></section>
      <section v-if="complaint.status === 'resolved'" class="card"><h2>处理情况</h2><dl><div><dt>处理结果</dt><dd>{{ complaint.handlingResultText }}</dd></div><div><dt>处理意见</dt><dd class="plain-text">{{ complaint.handlingOpinion || '--' }}</dd></div></dl></section>
      <section class="card"><h2>投诉附件</h2><article v-for="file in complaint.attachments" :key="file.id" class="file"><span>{{ file.name || `附件 ${file.id}` }}</span><div><button type="button" @click="preview(file)">预览</button><button type="button" @click="download(file)">下载</button></div></article><p v-if="!complaint.attachments.length">暂无附件。</p></section>
      <div class="actions"><RouterLink to="/student/complaints">返回投诉记录</RouterLink></div>
    </template>
  </div></main>
</template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,920px);margin:auto}header{display:flex;align-items:center;justify-content:space-between;gap:16px}.eyebrow{margin:0;color:#2563eb;font-size:12px;font-weight:800}.status{padding:7px 12px;border-radius:999px;color:#1d4ed8;background:#dbeafe;font-weight:700}.card,.state{margin:18px 0;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}dl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}dt{color:#64748b}dd{margin:5px 0}.plain-text{white-space:pre-wrap;overflow-wrap:anywhere}.file{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px;background:#f8fafc}.file div{display:flex;gap:8px}.file button,.actions a,.state a{padding:9px 14px;border:1px solid #cbd5e1;border-radius:8px;color:#2563eb;background:#fff;font-weight:700;text-decoration:none}.actions{display:flex;justify-content:flex-end}.state{text-align:center;color:#64748b}.error{color:#b91c1c}@media(max-width:640px){dl{grid-template-columns:1fr}.file{align-items:flex-start;flex-direction:column}}</style>
