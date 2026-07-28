<script setup>
import { onMounted, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { getAdminComplaints } from '../api/complaintApi.js'
import { adaptComplaintList } from '../adapters/complaintAdapter.js'

const items = ref([])
onMounted(async () => {
  try { items.value = adaptComplaintList(await getAdminComplaints({ page_size: 100 })) }
  catch (error) { window.alert(error?.message || '投诉列表加载失败') }
})
</script>

<template><main class="page"><div class="content">
  <header><div><p class="eyebrow">A801 · COMPLAINT MANAGEMENT</p><h1>投诉管理</h1><p>基础版仅支持查看匿名投诉。</p></div><RouterLink to="/admin/appeals-complaints">返回</RouterLink></header>
  <section class="panel"><table><thead><tr><th>投诉编号</th><th>提交方式</th><th>提交时间</th><th>状态</th><th>操作</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td>{{ item.id }}</td><td>匿名</td><td>{{ item.submitTime }}</td><td><StatusTag :status="item.status" /></td><td><RouterLink :to="`/admin/appeals-complaints/complaints/${item.id}`">查看详情</RouterLink></td></tr><tr v-if="!items.length"><td colspan="5">暂无投诉记录</td></tr></tbody></table></section>
</div></main></template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1100px);margin:auto}header{display:flex;justify-content:space-between}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.panel{margin-top:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}table{width:100%;border-collapse:collapse}th,td{padding:13px;border-bottom:1px solid #e2e8f0;text-align:left}a{color:#2563eb;font-weight:700;text-decoration:none}</style>
