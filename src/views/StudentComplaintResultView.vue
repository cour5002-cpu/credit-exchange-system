<script setup>
import { useRoute } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
const route = useRoute()
const complaint = { id: route.params.id, status: route.query.status || 'submitted', submitTime: new Date().toLocaleString('zh-CN', { hour12: false }) }
</script>

<template><main class="page"><section class="result"><div class="icon">✓</div><h1>投诉提交成功</h1><p>匿名投诉已提交至管理员端。</p><dl><div><dt>投诉编号</dt><dd>{{ complaint.id }}</dd></div><div><dt>提交时间</dt><dd>{{ complaint.submitTime }}</dd></div><div><dt>当前状态</dt><dd><StatusTag :status="complaint.status" /></dd></div></dl><div class="actions"><RouterLink to="/student/feedback">返回问题反馈</RouterLink><RouterLink class="primary" to="/student/dashboard">返回学生首页</RouterLink></div></section></main></template>

<style scoped>.page{min-height:100vh;display:grid;place-items:center;padding:24px;background:#f3f6fb}.result{width:min(100%,620px);padding:38px;border:1px solid #e2e8f0;border-radius:18px;background:#fff;text-align:center}.icon{display:grid;place-items:center;width:58px;height:58px;margin:0 auto 18px;border-radius:50%;color:#fff;background:#16a34a;font-size:30px}.result>p{color:#64748b}dl{margin:26px 0;text-align:left}dl div{display:flex;justify-content:space-between;padding:13px;border-bottom:1px solid #e2e8f0}dd{margin:0;font-weight:700}.actions{display:flex;justify-content:center;gap:10px}.actions a{padding:10px 15px;border:1px solid #cbd5e1;border-radius:9px;color:#2563eb;text-decoration:none;font-weight:700}.actions .primary{border-color:#2563eb;color:#fff;background:#2563eb}</style>
