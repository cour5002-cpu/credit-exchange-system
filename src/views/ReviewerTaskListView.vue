<script setup>
import { computed, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { currentReviewerId, getReviewerPendingApplications, mockReviewers } from '../mock/applications.js'
import { getReviewerPendingAppeals } from '../mock/appeals.js'

const keyword = ref('')
const reviewType = ref('')
const status = ref('')

const allItems = computed(() => [
  ...getReviewerPendingApplications(currentReviewerId.value).map((item) => ({
    key: `normal-${item.id}`, id: item.id, reviewType: 'normal', reviewTypeText: '普通审核', title: item.title,
    studentName: item.studentName, sourceText: item.sourceText || '课时申请', hours: item.requestedHours,
    assignTime: item.adminAcceptTime, status: item.status, detailTo: `/reviewer/review-tasks/${item.id}`,
  })),
  ...getReviewerPendingAppeals(currentReviewerId.value).map((item) => ({
    key: `appeal-${item.appealId}`, id: item.appealId, reviewType: 'appeal', reviewTypeText: '申诉复审', title: item.applicationTitle,
    studentName: item.studentName, sourceText: '学生课时认定申诉', hours: item.originalFinalHours,
    assignTime: item.reviewAssignTime, status: item.status, detailTo: `/reviewer/appeal-reviews/${item.appealId}`,
  })),
])

const items = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return allItems.value.filter((item) => (!reviewType.value || item.reviewType === reviewType.value)
    && (!status.value || item.status === status.value)
    && (!search || item.studentName.toLowerCase().includes(search) || item.title.toLowerCase().includes(search)))
})
</script>

<template><main class="review-page"><div class="page-content">
  <header class="page-header"><div><p class="eyebrow">R101 · REVIEW TASKS</p><h1>待审核成果</h1><p>统一处理课时申请成果材料审核与申诉复审；项目成果上传由指导老师确认。</p></div><RouterLink class="back-link" to="/reviewer/dashboard">返回审核首页</RouterLink></header>
  <section class="reviewer-switcher"><label><span>当前审核老师</span><select v-model="currentReviewerId"><option v-for="reviewer in mockReviewers" :key="reviewer.reviewerId" :value="reviewer.reviewerId">{{ reviewer.reviewerName }} · {{ reviewer.college }} · {{ reviewer.direction }}</option></select></label></section>
  <section class="filters"><label><span>审核类型</span><select v-model="reviewType"><option value="">全部</option><option value="normal">普通审核</option><option value="appeal">申诉复审</option></select></label><label><span>当前状态</span><select v-model="status"><option value="">全部状态</option><option value="pending_reviewer">待审核老师审核</option><option value="pending_re_review">等待复审</option></select></label><label><span>搜索</span><input v-model="keyword" type="search" placeholder="搜索学生姓名或申请名称" /></label></section>
  <section class="list-panel"><div class="panel-header"><h2>待审核列表</h2><span>共 {{ items.length }} 项</span></div><div class="table-wrapper"><table><thead><tr><th>编号</th><th>审核类型</th><th>关联申请名称</th><th>学生姓名</th><th>申请 / 申诉来源</th><th>申请 / 原认定课时</th><th>分配时间</th><th>当前状态</th><th>操作</th></tr></thead><tbody><tr v-for="item in items" :key="item.key"><td>{{ item.id }}</td><td><span class="type-tag" :class="`type-tag--${item.reviewType}`">{{ item.reviewTypeText }}</span></td><td>{{ item.title }}</td><td>{{ item.studentName }}</td><td>{{ item.sourceText }}</td><td>{{ item.hours ?? '--' }} 课时</td><td>{{ item.assignTime || '--' }}</td><td><StatusTag :status="item.status" /></td><td><RouterLink class="detail-link" :to="item.detailTo">查看详情</RouterLink></td></tr><tr v-if="!items.length"><td class="empty" colspan="9">暂无分配给当前审核老师的待审核任务。</td></tr></tbody></table></div></section>
</div></main></template>

<style scoped>
.review-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.page-content{width:min(100%,1240px);margin:auto}.page-header{display:flex;justify-content:space-between;gap:24px;margin-bottom:24px}.page-header h1{margin:0 0 8px}.page-header p{color:#64748b}.eyebrow{margin:0 0 7px!important;color:#2563eb!important;font-size:12px;font-weight:800}.back-link,.detail-link{color:#2563eb;font-weight:700;text-decoration:none}.back-link{height:max-content;padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.reviewer-switcher,.filters{margin-bottom:16px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.reviewer-switcher{border-color:#bfdbfe;background:#eff6ff}.reviewer-switcher span,.filters span{display:block;margin-bottom:7px;font-weight:700}.reviewer-switcher select,.filters select,.filters input{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.filters{display:grid;grid-template-columns:220px 240px 1fr;gap:16px}.list-panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-header{display:flex;justify-content:space-between;padding:18px 20px}.panel-header h2{margin:0}.panel-header span{color:#64748b}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:13px;border-top:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc;font-size:13px}.type-tag{padding:5px 9px;border-radius:999px;font-size:12px;font-weight:700}.type-tag--normal{color:#166534;background:#dcfce7}.type-tag--appeal{color:#7c3aed;background:#ede9fe}.empty{text-align:center;color:#64748b}@media(max-width:760px){.review-page{padding:24px 14px}.page-header{flex-direction:column}.filters{grid-template-columns:1fr}}
</style>
