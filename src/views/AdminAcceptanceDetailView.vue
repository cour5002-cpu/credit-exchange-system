<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ReviewActionBar from '../components/ReviewActionBar.vue'
import StatusTag from '../components/StatusTag.vue'
import { getAcceptanceTypeText, getAdminAcceptance } from '../mock/adminAcceptances'

const route = useRoute()
const router = useRouter()
const item = computed(() => getAdminAcceptance(route.params.id))
const opinion = ref('')
const feedback = ref({ type: '', message: '' })

function acceptApplication() { if (!item.value) return; item.value.status = 'accepted'; feedback.value = { type: 'success', message: '受理通过成功' }; window.alert(feedback.value.message) }
function rejectApplication() { if (!opinion.value.trim()) { feedback.value = { type: 'error', message: '请填写驳回原因' }; window.alert(feedback.value.message); return } item.value.status = 'rejected'; feedback.value = { type: 'success', message: '驳回成功' }; window.alert(feedback.value.message) }
function previewFile(file) { window.alert(`正在预览：${file.name}`) }
function downloadFile(file) { window.alert(`正在下载：${file.name}`) }
function goBack() { router.push('/admin/review-assign') }
</script>

<template>
  <main class="detail-page"><div class="detail-content">
    <template v-if="item">
      <header class="page-header"><div><p class="eyebrow">ACCEPTANCE DETAIL</p><h1>{{ item.title }}</h1><p>{{ getAcceptanceTypeText(item.type) }}</p></div><StatusTag :status="item.status" /></header>
      <section class="card"><h2>学生信息</h2><dl class="info-grid"><div><dt>姓名</dt><dd>{{ item.student.name }}</dd></div><div><dt>学号</dt><dd>{{ item.student.studentNo }}</dd></div><div><dt>学院</dt><dd>{{ item.student.college }}</dd></div><div><dt>专业</dt><dd>{{ item.student.major }}</dd></div></dl></section>
      <section class="card"><h2>申请信息</h2><dl class="info-grid"><div><dt>申请编号</dt><dd>{{ item.id }}</dd></div><div><dt>申请来源</dt><dd>{{ item.application.source }}</dd></div><div><dt>申请类别</dt><dd>{{ item.application.category }}</dd></div><div><dt>申请课时</dt><dd>{{ item.application.requestedHours }} 小时</dd></div><div v-if="item.application.requestedCredits"><dt>兑换学分</dt><dd>{{ item.application.requestedCredits }} 学分</dd></div><div><dt>提交时间</dt><dd>{{ item.submittedAt }}</dd></div></dl><p class="description">{{ item.application.description }}</p></section>
      <section class="card"><h2>团队成员</h2><div class="table-wrapper"><table><thead><tr><th>姓名</th><th>学号</th><th>学院</th><th>专业</th><th>角色</th></tr></thead><tbody><tr v-for="member in item.members" :key="member.studentNo"><td>{{ member.name }}</td><td>{{ member.studentNo }}</td><td>{{ member.college }}</td><td>{{ member.major }}</td><td>{{ member.isLeader ? '队长' : '成员' }}</td></tr></tbody></table></div></section>
      <section class="card"><h2>指导老师确认意见</h2><dl class="info-grid"><div><dt>指导老师</dt><dd>{{ item.teacher.name }} · {{ item.teacher.department }}</dd></div><div><dt>确认时间</dt><dd>{{ item.teacher.confirmedAt }}</dd></div></dl><p class="teacher-opinion">{{ item.teacher.opinion }}</p></section>
      <section class="card"><h2>学生上传材料</h2><div v-if="item.attachments?.length" class="attachment-list"><article v-for="file in item.attachments" :key="file.id" class="attachment-item"><div class="file-icon">文</div><div><h3>{{ file.name }}</h3><p class="meta">{{ file.type }} · 上传时间：{{ file.uploadedAt }}</p><p>{{ file.description }}</p></div><div class="file-actions"><button type="button" @click="previewFile(file)">预览</button><button type="button" @click="downloadFile(file)">下载</button></div></article></div><p v-else class="empty">暂无上传材料</p></section>
      <section class="card"><label for="acceptance-opinion"><strong>管理员受理意见</strong></label><textarea id="acceptance-opinion" v-model="opinion" rows="5" placeholder="请输入受理意见；驳回时必须填写驳回原因。"></textarea><p v-if="feedback.message" class="feedback" :class="`feedback--${feedback.type}`">{{ feedback.message }}</p></section>
      <ReviewActionBar approve-text="受理通过" reject-text="驳回" @approve="acceptApplication" @reject="rejectApplication"><template #before><button class="back-button" type="button" @click="goBack">返回</button></template></ReviewActionBar>
    </template>
    <section v-else class="not-found"><h1>未找到受理申请</h1><button class="back-button" type="button" @click="goBack">返回待受理列表</button></section>
  </div></main>
</template>

<style scoped>
.detail-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.detail-content{width:min(100%,960px);margin:0 auto}.page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:22px}.page-header h1{margin:0 0 8px;font-size:29px}.page-header p{margin:0;color:#64748b}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px;font-size:19px}.info-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.info-grid dt{margin-bottom:5px;color:#64748b;font-size:13px}.info-grid dd{margin:0;font-weight:600}.description,.teacher-opinion{margin:18px 0 0;padding-top:16px;border-top:1px solid #e2e8f0;color:#475569;line-height:1.7}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px 12px;border-bottom:1px solid #e2e8f0;text-align:left}th{color:#475569;background:#f8fafc;font-size:13px}.attachment-list{display:grid;gap:12px}.attachment-item{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:14px;padding:15px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.file-icon{display:grid;width:40px;height:40px;place-items:center;border-radius:9px;color:#1d4ed8;background:#dbeafe;font-weight:800}.attachment-item h3{margin:0;font-size:15px}.attachment-item p{margin:5px 0 0;color:#475569;font-size:13px}.attachment-item .meta{color:#64748b;font-size:12px}.file-actions{display:flex;gap:8px}.file-actions button{padding:7px 11px;border:1px solid #bfdbfe;border-radius:8px;color:#1d4ed8;background:#fff;font-weight:700;cursor:pointer}.empty{padding:28px;color:#64748b;background:#f8fafc;text-align:center}textarea{width:100%;margin-top:10px;padding:11px 12px;border:1px solid #cbd5e1;border-radius:9px;resize:vertical;font:inherit}.feedback{padding:10px 12px;border-radius:8px}.feedback--error{color:#b91c1c;background:#fef2f2}.feedback--success{color:#166534;background:#f0fdf4}.back-button{padding:10px 18px;border:1px solid #cbd5e1;border-radius:10px;color:#334155;background:#fff;font:inherit;font-weight:700;cursor:pointer}.not-found{padding:40px;border-radius:14px;background:#fff;text-align:center}@media(max-width:700px){.detail-page{padding:24px 14px}.info-grid{grid-template-columns:1fr}.attachment-item{grid-template-columns:auto 1fr}.file-actions{grid-column:1/-1;justify-content:flex-end}}
</style>

