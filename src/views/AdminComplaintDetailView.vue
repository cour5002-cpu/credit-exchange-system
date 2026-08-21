<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAdminComplaint, resolveComplaint, startProcessingComplaint } from '../api/complaintApi.js'
import { downloadAttachment, getAttachmentErrorMessage, previewAttachment } from '../api/fileApi.js'
import { adaptComplaintEnvelope } from '../adapters/complaintAdapter.js'

const route = useRoute()
const router = useRouter()
const complaint = ref(null)
const loading = ref(true)
const operationLoading = ref(false)
const errorMessage = ref('')
const operationMessage = ref('')
const resolveForm = reactive({ handlingResult: '', handlingOpinion: '' })

function errorText(error) {
  const responseStatus = Number(error?.status ?? error?.response?.status)
  if (responseStatus === 401) return error?.message || '登录已过期，请重新登录。'
  if (responseStatus === 403) return '无权限查看或处理该投诉。'
  if (responseStatus === 404) return '投诉不存在或不可见。'
  return error?.message || '投诉详情加载失败。'
}

async function loadComplaint() {
  loading.value = true
  complaint.value = null
  errorMessage.value = ''
  try {
    complaint.value = adaptComplaintEnvelope(await getAdminComplaint(route.params.id))
    if (!complaint.value) errorMessage.value = '投诉不存在或不可见。'
  } catch (error) {
    complaint.value = null
    errorMessage.value = errorText(error)
  } finally {
    loading.value = false
  }
}

async function startProcessing() {
  operationLoading.value = true
  operationMessage.value = ''
  try {
    await startProcessingComplaint(complaint.value.id)
    await loadComplaint()
  } catch (error) {
    operationMessage.value = errorText(error)
    if (Number(error?.status ?? error?.response?.status) === 409) await loadComplaint()
  } finally {
    operationLoading.value = false
  }
}

async function resolve() {
  const opinion = resolveForm.handlingOpinion.trim()
  if (!resolveForm.handlingResult) return operationMessage.value = '请选择处理结果。'
  if (!opinion) return operationMessage.value = '请填写处理意见。'
  if (opinion.length > 4000) return operationMessage.value = '处理意见最多 4000 个字符。'
  operationLoading.value = true
  operationMessage.value = ''
  try {
    await resolveComplaint(complaint.value.id, {
      handling_result: resolveForm.handlingResult,
      handling_opinion: opinion,
    })
    await loadComplaint()
  } catch (error) {
    operationMessage.value = errorText(error)
    if (Number(error?.status ?? error?.response?.status) === 409) await loadComplaint()
  } finally {
    operationLoading.value = false
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
    <section v-if="loading" class="card state">投诉详情加载中...</section>
    <section v-else-if="errorMessage" class="card state error" role="alert"><p>{{ errorMessage }}</p><button type="button" @click="router.push('/admin/appeals-complaints/complaints')">返回投诉列表</button></section>
    <template v-else-if="complaint">
      <header><div><p class="eyebrow">A802 · COMPLAINT DETAIL</p><h1>投诉详情</h1><p>{{ complaint.complaintNo || '--' }}</p></div><span class="status">{{ complaint.statusText }}</span></header>
      <section class="card"><h2>投诉基本信息</h2><dl><div><dt>投诉编号</dt><dd>{{ complaint.complaintNo || '--' }}</dd></div><div><dt>投诉分类</dt><dd>{{ complaint.categoryText }}</dd></div><div><dt>当前状态</dt><dd>{{ complaint.statusText }}</dd></div><div><dt>提交时间</dt><dd>{{ complaint.submittedAt || complaint.createdAt || '--' }}</dd></div></dl></section>
      <section class="card"><h2>实名提交人</h2><dl><div><dt>姓名</dt><dd>{{ complaint.submitter?.name || '--' }}</dd></div><div><dt>学号</dt><dd>{{ complaint.submitter?.studentNo || '--' }}</dd></div><div><dt>学生 ID</dt><dd>{{ complaint.submitter?.studentId || '--' }}</dd></div><div><dt>用户 ID</dt><dd>{{ complaint.submitter?.userId || '--' }}</dd></div></dl></section>
      <section class="card"><h2>投诉内容</h2><p class="plain-text">{{ complaint.content }}</p></section>
      <section class="card"><h2>投诉材料</h2><article v-for="file in complaint.attachments" :key="file.id" class="file"><span>{{ file.name || file.fileName || `附件 ${file.id}` }}</span><div class="file-actions"><button type="button" @click="preview(file)">预览</button><button type="button" @click="download(file)">下载</button></div></article><p v-if="!complaint.attachments.length">暂无附件材料</p></section>
      <section v-if="complaint.status === 'submitted'" class="card"><h2>投诉处理</h2><button class="primary" type="button" :disabled="operationLoading" @click="startProcessing">{{ operationLoading ? '处理中...' : '开始处理' }}</button></section>
      <form v-else-if="complaint.status === 'processing'" class="card" @submit.prevent="resolve"><h2>完成处理</h2><label><span>处理结果</span><select v-model="resolveForm.handlingResult"><option value="" disabled>请选择处理结果</option><option value="substantiated">投诉成立</option><option value="partially_substantiated">部分成立</option><option value="unsubstantiated">投诉不成立</option><option value="transferred">已转交其他渠道</option><option value="other">其他处理结果</option></select></label><label><span>处理意见</span><textarea v-model="resolveForm.handlingOpinion" rows="6" maxlength="4000" placeholder="请填写处理意见"></textarea><small>{{ resolveForm.handlingOpinion.length }} / 4000</small></label><button class="primary" type="submit" :disabled="operationLoading">{{ operationLoading ? '提交中...' : '完成处理' }}</button></form>
      <section v-else-if="complaint.status === 'resolved'" class="card"><h2>处理信息</h2><dl><div><dt>处理结果</dt><dd>{{ complaint.handlingResultText }}</dd></div><div><dt>开始处理时间</dt><dd>{{ complaint.processingStartedAt || '--' }}</dd></div><div><dt>处理完成时间</dt><dd>{{ complaint.resolvedAt || '--' }}</dd></div><div class="wide"><dt>处理意见</dt><dd class="plain-text">{{ complaint.handlingOpinion || '--' }}</dd></div></dl></section>
      <p v-if="operationMessage" class="operation-error" role="alert">{{ operationMessage }}</p>
      <div class="actions"><button type="button" @click="router.push('/admin/appeals-complaints/complaints')">返回</button></div>
    </template>
  </div></main>
</template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,920px);margin:auto}header{display:flex;justify-content:space-between}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.status{align-self:flex-start;padding:7px 12px;border-radius:999px;color:#1d4ed8;background:#dbeafe;font-weight:700}.card{margin:18px 0;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}dl{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.wide{grid-column:1/-1}dt{color:#64748b}dd{margin:5px 0}.plain-text{white-space:pre-wrap;overflow-wrap:anywhere}.file{display:flex;justify-content:space-between;padding:12px;background:#f8fafc}.file-actions{display:flex;gap:8px}form label{display:grid;gap:7px;margin:14px 0}select,textarea{box-sizing:border-box;width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px}.actions{display:flex;justify-content:flex-end}.actions button,.file button,.state button,.primary{padding:9px 15px;border:1px solid #cbd5e1;border-radius:8px;background:#fff}.primary{border-color:#2563eb;color:#fff;background:#2563eb;font-weight:700}.state{text-align:center}.error,.operation-error{color:#b91c1c}.operation-error{padding:12px;border-radius:8px;background:#fef2f2}@media(max-width:640px){dl{grid-template-columns:1fr}.wide{grid-column:auto}}</style>
