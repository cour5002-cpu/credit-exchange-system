<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ReviewActionBar from '../components/ReviewActionBar.vue'
import StatusTag from '../components/StatusTag.vue'
import { loadReviewerOptions } from '../services/commonDependencyService.js'
import { assignApplicationReviewer, getAdminApplication } from '../api/applicationApi.js'
import { adaptApplicationEnvelope } from '../adapters/applicationAdapter.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const route = useRoute()
const router = useRouter()
const item = ref(null)
const opinion = ref('')
const selectedReviewerId = ref('')
const feedback = ref({ type: '', message: '' })
const reviewers = ref([])
const canAssign = computed(() => Boolean(item.value && (
  item.value.actions?.can_assign === true
  || (item.value.canOperate === true && item.value.status === 'pending_assignment')
)))
async function loadItem(){try{item.value=adaptApplicationEnvelope(await getAdminApplication(Number(route.params.id)))}catch(error){window.alert(getApiErrorMessage(error,'申请详情加载失败'))}}
onMounted(async () => {
  const loadedReviewers = await loadReviewerOptions()
  reviewers.value = loadedReviewers.filter((reviewer) => Number.isInteger(reviewer.id) && reviewer.id > 0 && !reviewer.isMockFallback)
  await loadItem()
})

async function acceptApplication() {
  if (!selectedReviewerId.value) {
    feedback.value = { type: 'error', message: '请选择审核老师' }
    window.alert(feedback.value.message)
    return
  }
  if (!item.value || !canAssign.value) return window.alert('当前申请不可分配，请刷新后重试')
  const reviewerTeacherId = selectedReviewerId.value
  if (!Number.isInteger(reviewerTeacherId) || reviewerTeacherId <= 0) return window.alert('请选择审核老师')
  try {
    await assignApplicationReviewer(item.value.id, { reviewer_teacher_id: reviewerTeacherId, comment: opinion.value.trim() })
    window.alert('分配成功')
    goBack()
  } catch (error) {
    if (error?.code === 40301 || error?.status === 403 || error?.category === 'forbidden') {
      return window.alert('无权限执行分配操作，请重新登录管理员账号')
    }
    window.alert(getApiErrorMessage(error, '分配失败'))
  }
}
function previewFile() { window.alert('当前为 Mock 附件预览，真实预览需后端文件服务支持。') }
function downloadFile() { window.alert('当前为 Mock 附件下载，真实下载需后端文件服务支持。') }
function goBack() { router.push('/admin/review-assign') }
</script>

<template>
  <main class="detail-page"><div class="detail-content">
    <template v-if="item">
      <header class="page-header"><div><p class="eyebrow">REVIEW ASSIGNMENT DETAIL</p><h1>{{ item.title }}</h1><p>{{ item.applyTypeText }}</p></div><StatusTag :status="item.status" /></header>
      <section class="card"><h2>学生信息</h2><dl class="info-grid"><div><dt>姓名</dt><dd>{{ item.studentName }}</dd></div><div><dt>学号</dt><dd>{{ item.studentId }}</dd></div><div><dt>申请人身份</dt><dd>{{ item.captainId === item.currentUserId ? '队长' : '成员' }}</dd></div><div><dt>当前流程</dt><dd>管理员分配审核老师</dd></div></dl></section>
      <section class="card"><h2>申请信息</h2><dl class="info-grid"><div><dt>申请编号</dt><dd>{{ item.id }}</dd></div><div><dt>申请来源</dt><dd>{{ item.sourceText }}</dd></div><div><dt>申请类型</dt><dd>{{ item.applyTypeText }}</dd></div><div><dt>申请课时</dt><dd>{{ item.requestedHours }} 小时</dd></div><div v-if="item.taskId"><dt>关联任务</dt><dd>{{ item.taskTitle }}（{{ item.taskId }}）</dd></div><div><dt>提交时间</dt><dd>{{ item.submitTime }}</dd></div></dl></section>
      <section v-if="item.applicationType === 'task_result'" class="card"><h2>任务成果说明</h2><p class="description">{{ item.resultDescription || '--' }}</p></section>
      <section class="card"><h2>团队成员</h2><div class="table-wrapper"><table><thead><tr><th>姓名</th><th>学号</th><th>学院</th><th>专业</th><th>角色</th></tr></thead><tbody><tr v-for="member in item.members" :key="member.id"><td>{{ member.name }}</td><td>{{ member.studentId }}</td><td>{{ member.college || '--' }}</td><td>{{ member.major || '--' }}</td><td>{{ member.role === 'captain' ? '队长' : '成员' }}</td></tr></tbody></table></div></section>
      <section class="card"><h2>指导老师确认意见</h2><dl class="info-grid"><div><dt>指导老师</dt><dd>{{ item.mainAdvisor?.name || '--' }} · {{ item.mainAdvisor?.department || '--' }}</dd></div><div><dt>确认状态</dt><dd><StatusTag :status="item.advisorStatus" text="已确认" /></dd></div><div><dt>确认时间</dt><dd>{{ item.advisorConfirmTime || '--' }}</dd></div></dl><p class="teacher-opinion">{{ item.advisorComment || '指导老师未填写确认意见。' }}</p></section>
      <section class="card"><h2>学生上传材料</h2><div v-if="item.attachments?.length" class="attachment-list"><article v-for="file in item.attachments" :key="file.id" class="attachment-item"><div class="file-icon">文</div><div><h3>{{ file.name }}</h3><p class="meta">{{ file.type }}<template v-if="file.uploadedAt"> · 上传时间：{{ file.uploadedAt }}</template></p><p>{{ file.description }}</p></div><div class="file-actions"><button type="button" @click="previewFile(file)">预览</button><button type="button" @click="downloadFile(file)">下载</button></div></article></div><p v-else class="empty">暂无上传材料</p></section>
      <section class="card reviewer-assignment"><label for="assigned-reviewer"><strong>选择审核老师 <span class="required">*</span></strong></label><select id="assigned-reviewer" v-model="selectedReviewerId"><option value="">请选择审核老师</option><option v-for="reviewer in reviewers" :key="reviewer.reviewerId" :value="reviewer.reviewerId">{{ reviewer.reviewerName }} · {{ reviewer.college || '未设置学院' }} · {{ reviewer.direction || '未设置方向' }}（待处理 {{ reviewer.pendingCount }} 项）</option></select><p>请从系统审核老师池中选择，确认后申请将进入审核老师审核。</p></section>
      <section class="acceptance-notice">管理员在此阶段分配审核老师，不在此阶段驳回申请。</section>
      <section class="card"><label for="acceptance-opinion"><strong>管理员分配意见</strong></label><textarea id="acceptance-opinion" v-model="opinion" rows="5" placeholder="请输入分配说明。"></textarea><p v-if="feedback.message" class="feedback" :class="`feedback--${feedback.type}`">{{ feedback.message }}</p></section>
      <ReviewActionBar approve-text="确认分配" :show-reject="false" :approve-disabled="!canAssign" @approve="acceptApplication"><template #before><button class="back-button" type="button" @click="goBack">返回</button></template></ReviewActionBar>
    </template>
    <section v-else class="not-found"><h1>未找到待分配申请</h1><button class="back-button" type="button" @click="goBack">返回审核分配列表</button></section>
  </div></main>
</template>

<style scoped>
.detail-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.detail-content{width:min(100%,960px);margin:0 auto}.page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:22px}.page-header h1{margin:0 0 8px;font-size:29px}.page-header p{margin:0;color:#64748b}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px;font-size:19px}.info-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.info-grid dt{margin-bottom:5px;color:#64748b;font-size:13px}.info-grid dd{margin:0;font-weight:600}.description,.teacher-opinion{margin:18px 0 0;padding-top:16px;border-top:1px solid #e2e8f0;color:#475569;line-height:1.7}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px 12px;border-bottom:1px solid #e2e8f0;text-align:left}th{color:#475569;background:#f8fafc;font-size:13px}.attachment-list{display:grid;gap:12px}.attachment-item{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:14px;padding:15px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.file-icon{display:grid;width:40px;height:40px;place-items:center;border-radius:9px;color:#1d4ed8;background:#dbeafe;font-weight:800}.attachment-item h3{margin:0;font-size:15px}.attachment-item p{margin:5px 0 0;color:#475569;font-size:13px}.attachment-item .meta{color:#64748b;font-size:12px}.file-actions{display:flex;gap:8px}.file-actions button{padding:7px 11px;border:1px solid #bfdbfe;border-radius:8px;color:#1d4ed8;background:#fff;font-weight:700;cursor:pointer}.empty{padding:28px;color:#64748b;background:#f8fafc;text-align:center}textarea{width:100%;margin-top:10px;padding:11px 12px;border:1px solid #cbd5e1;border-radius:9px;resize:vertical;font:inherit}.feedback{padding:10px 12px;border-radius:8px}.feedback--error{color:#b91c1c;background:#fef2f2}.feedback--success{color:#166534;background:#f0fdf4}.back-button{padding:10px 18px;border:1px solid #cbd5e1;border-radius:10px;color:#334155;background:#fff;font:inherit;font-weight:700;cursor:pointer}.not-found{padding:40px;border-radius:14px;background:#fff;text-align:center}@media(max-width:700px){.detail-page{padding:24px 14px}.info-grid{grid-template-columns:1fr}.attachment-item{grid-template-columns:auto 1fr}.file-actions{grid-column:1/-1;justify-content:flex-end}}
.reviewer-assignment select{width:100%;margin-top:10px;padding:11px 12px;border:1px solid #cbd5e1;border-radius:9px;background:#fff;font:inherit}.reviewer-assignment p{margin:9px 0 0;color:#64748b;font-size:13px}.required{color:#dc2626}
.acceptance-notice{margin-bottom:18px;padding:12px 16px;border:1px solid #bfdbfe;border-radius:10px;color:#1d4ed8;background:#eff6ff}
</style>
