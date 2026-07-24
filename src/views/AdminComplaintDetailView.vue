<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { getComplaintById, markComplaintViewed } from '../mock/complaints.js'
const route = useRoute(); const router = useRouter()
const complaint = computed(() => markComplaintViewed(route.params.id) || getComplaintById(route.params.id))
function preview() { window.alert('当前为 Mock 附件预览。') }
</script>
<template><main class="page"><div class="content"><template v-if="complaint"><header><div><p class="eyebrow">A802 · COMPLAINT DETAIL</p><h1>投诉详情</h1><p>{{ complaint.complaintId }}</p></div><StatusTag :status="complaint.status" /></header><section class="card"><h2>投诉基本信息</h2><dl><div><dt>提交方式</dt><dd>匿名投诉</dd></div><div><dt>提交时间</dt><dd>{{ complaint.submitTime }}</dd></div><div><dt>当前状态</dt><dd>已查看</dd></div></dl></section><section class="card"><h2>投诉内容</h2><p>{{ complaint.complaintContent }}</p></section><section class="card"><h2>投诉材料</h2><article v-for="file in complaint.complaintMaterials" :key="file.id" class="file"><span>{{ file.fileName }}</span><button @click="preview">预览</button></article><p v-if="!complaint.complaintMaterials.length">暂无附件材料</p></section><div class="actions"><button @click="router.push('/admin/appeals-complaints/complaints')">返回</button></div></template></div></main></template>
<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,920px);margin:auto}header{display:flex;justify-content:space-between}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.card{margin:18px 0;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}dl{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}dt{color:#64748b}dd{margin:5px 0}.file{display:flex;justify-content:space-between;padding:12px;background:#f8fafc}.actions{display:flex;justify-content:flex-end}.actions button,.file button{padding:9px 15px;border:1px solid #cbd5e1;border-radius:8px;background:#fff}</style>
