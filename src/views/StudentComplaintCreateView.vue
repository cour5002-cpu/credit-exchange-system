<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { submitComplaint } from '../api/complaintApi.js'
import { uploadAttachment } from '../api/fileApi.js'

const router = useRouter()
const form = reactive({ content: '', contactQq: '', files: [], attachmentIds: [] })

async function selectFiles(event) {
  for (const file of Array.from(event.target.files || [])) {
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
  if (!form.content.trim()) return window.alert('请填写投诉内容。')
  if (!form.contactQq.trim()) return window.alert('请填写联系 QQ 号。')
  try {
    const complaint = await submitComplaint({
      content: form.content.trim(),
      contact_qq: form.contactQq.trim(),
      attachment_ids: form.attachmentIds,
    })
    await router.push(`/student/complaints/submitted/${complaint.id}?status=${complaint.status || 'submitted'}`)
  } catch (error) { window.alert(error?.message || '投诉提交失败') }
}
</script>

<template><main class="page"><div class="content">
  <header><div><p class="eyebrow">S801 · ANONYMOUS COMPLAINT</p><h1>发起问题反馈与投诉</h1><p>提交投诉内容、联系 QQ 和相关附件。</p></div><RouterLink to="/student/feedback">返回问题反馈</RouterLink></header>
  <section class="notice"><strong>匿名提示</strong><p>投诉不会提交姓名、学号或用户账号；联系 QQ 仅供管理员跟进投诉时使用。</p></section>
  <section class="card"><h2>联系 QQ</h2><input v-model="form.contactQq" type="text" inputmode="numeric" autocomplete="off" placeholder="请输入可联系的 QQ 号" /></section>
  <section class="card"><h2>投诉内容</h2><textarea v-model="form.content" rows="7" placeholder="请详细说明需要反馈的问题"></textarea></section>
  <section class="card"><h2>投诉材料（可选）</h2><input type="file" multiple @change="selectFiles" /><article v-for="file in form.files" :key="file.id" class="file"><span>{{ file.name }}</span><button type="button" @click="removeFile(file.id)">删除</button></article></section>
  <div class="actions"><RouterLink to="/student/feedback">返回</RouterLink><button type="button" @click="submit">提交问题反馈与投诉</button></div>
</div></main></template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,900px);margin:auto}header{display:flex;justify-content:space-between}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.notice,.card{margin:18px 0;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.notice{background:#eff6ff}textarea,input{box-sizing:border-box;width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:9px}.file{display:flex;justify-content:space-between;margin-top:10px;padding:12px;background:#f8fafc}.actions{display:flex;justify-content:flex-end;gap:10px}.actions a,.actions button,.file button{padding:9px 15px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;text-decoration:none}.actions>button{color:#fff;background:#2563eb}</style>
