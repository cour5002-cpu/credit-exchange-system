<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ReviewActionBar from '../components/ReviewActionBar.vue'
import StatusTag from '../components/StatusTag.vue'
import {
  APPLICATION_STATUS,
  finalApprove,
  finalReject,
  getApplications,
} from '../mock/applications.js'
import { finalApproveApplication, finalRejectApplication, getApplicationFinalReview } from '../api/applicationApi.js'
import { adaptApplicationEnvelope } from '../adapters/applicationAdapter.js'
import { getApiErrorMessage, hasServerAction } from '../utils/apiFeedback.js'
const route = useRoute(); const router = useRouter(); const item = ref(null); const opinion = ref(''); const feedback = ref('')
async function loadItem(){try{item.value=adaptApplicationEnvelope(await getApplicationFinalReview(Number(route.params.id)))}catch(error){window.alert(getApiErrorMessage(error,'最终确认详情加载失败'))}}
onMounted(loadItem)
const timeline = computed(() => item.value ? [
  { title: '学生提交申请', time: item.value.submitTime },
  { title: '指导老师确认通过', time: item.value.advisorConfirmTime },
  { title: '管理员受理并分配', time: item.value.adminAcceptTime },
  { title: item.value.reviewStatus === 'modified_approved' ? '审核老师修改课时后审核通过' : '审核老师审核通过', time: item.value.reviewTime },
].filter((record) => record.time) : [])
async function approve() { if (!item.value || !hasServerAction(item.value.actions,['final_approve','approve'],item.value.status==='pending_admin_final')) return;try{await finalApproveApplication(item.value.id,{comment:opinion.value.trim()});await loadItem();feedback.value='最终确认通过成功';window.alert(feedback.value)}catch(error){window.alert(getApiErrorMessage(error,'最终确认失败'))} }
async function reject() { if (!opinion.value.trim()) return window.alert('请填写最终确认意见');try{await finalRejectApplication(item.value.id,{comment:opinion.value.trim()});await loadItem();feedback.value='最终驳回成功';window.alert(feedback.value)}catch(error){window.alert(getApiErrorMessage(error,'最终驳回失败'))} }
function preview() { window.alert('当前为 Mock 附件预览，真实预览需后端文件服务支持。') } function download() { window.alert('当前为 Mock 附件下载，真实下载需后端文件服务支持。') } function goBack() { router.push('/admin/final-confirm') }
</script>
<template><main class="detail-page"><div class="content"><template v-if="item"><header class="page-header"><div><p class="eyebrow">FINAL CONFIRMATION DETAIL</p><h1>{{ item.title }}</h1><p>{{ item.sourceText }}</p></div><StatusTag :status="item.status" /></header>
<section class="card"><h2>学生信息</h2><dl class="grid"><div><dt>姓名</dt><dd>{{ item.studentName }}</dd></div><div><dt>学号</dt><dd>{{ item.studentId }}</dd></div><div><dt>申请人身份</dt><dd>{{ item.captainId === item.currentUserId ? '队长' : '成员' }}</dd></div><div><dt>提交时间</dt><dd>{{ item.submitTime }}</dd></div></dl></section>
<section class="card"><h2>申请信息</h2><dl class="grid"><div><dt>申请编号</dt><dd>{{ item.id }}</dd></div><div><dt>申请来源</dt><dd>{{ item.sourceText }}</dd></div><div><dt>申请类型</dt><dd>{{ item.applyTypeText }}</dd></div><div v-if="item.taskId"><dt>关联任务</dt><dd>{{ item.taskTitle }}（{{ item.taskId }}）</dd></div><div><dt>原申请课时</dt><dd>{{ item.originalHours }} 小时</dd></div><div><dt>审核认定课时</dt><dd>{{ item.recognizedHours }} 小时</dd></div><div><dt>审核结果</dt><dd><StatusTag :status="item.reviewStatus" :text="item.reviewStatus === 'modified_approved' ? '修改课时后审核通过' : '审核通过'" /></dd></div></dl></section>
<section class="card"><h2>团队成员</h2><div class="table-wrap"><table><thead><tr><th>姓名</th><th>学号</th><th>学院</th><th>专业</th><th>角色</th></tr></thead><tbody><tr v-for="member in item.members" :key="member.id"><td>{{ member.name }}</td><td>{{ member.studentId }}</td><td>{{ member.college || '--' }}</td><td>{{ member.major || '--' }}</td><td>{{ member.role === 'captain' ? '队长' : '成员' }}</td></tr></tbody></table></div></section>
<section class="card"><h2>处理意见</h2><div class="opinion"><strong>指导老师确认意见</strong><p>{{ item.mainAdvisor?.name || '--' }}：{{ item.advisorComment || '未填写确认意见' }}</p></div><div class="opinion"><strong>管理员受理意见</strong><p>{{ item.adminAcceptComment || '未填写受理意见' }}</p></div><div class="opinion"><strong>审核老师审核意见</strong><p>{{ item.reviewer?.name || '审核老师' }}：{{ item.reviewComment || '未填写审核意见' }}</p><p>原申请 {{ item.originalHours }} 课时，审核认定 {{ item.recognizedHours }} 课时。</p></div></section>
<section class="card"><h2>学生上传材料</h2><div v-if="item.attachments.length" class="files"><article v-for="file in item.attachments" :key="file.id"><div><strong>{{ file.name }}</strong><small>{{ file.type }}<template v-if="file.uploadedAt"> · {{ file.uploadedAt }}</template></small><p>{{ file.description }}</p></div><div><button @click="preview(file)">预览</button><button @click="download(file)">下载</button></div></article></div><p v-else class="empty">暂无上传材料</p></section>
<section class="card"><h2>流程记录</h2><ol class="timeline"><li v-for="record in timeline" :key="record.time"><span></span><div><strong>{{ record.title }}</strong><time>{{ record.time }}</time></div></li></ol></section>
<section class="card"><label for="final-opinion"><strong>管理员最终确认意见</strong></label><textarea id="final-opinion" v-model="opinion" rows="5" placeholder="请输入最终确认意见；最终驳回时必填。"></textarea><p v-if="feedback" class="feedback">{{ feedback }}</p></section>
<ReviewActionBar v-if="hasServerAction(item.actions,['final_approve','approve'],item.status === 'pending_admin_final')" approve-text="最终确认通过" reject-text="最终驳回" @approve="approve" @reject="reject"><template #before><button class="back-button" @click="goBack">返回</button></template></ReviewActionBar><div v-else class="actions"><button class="back-button" @click="goBack">返回</button></div>
</template><section v-else class="card empty"><h1>未找到最终确认申请</h1><button class="back-button" @click="goBack">返回</button></section></div></main></template>
<style scoped>
.detail-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,960px);margin:auto}.page-header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}.page-header h1{margin:0}.page-header p{color:#64748b}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px;font-size:19px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.grid dt{color:#64748b;font-size:13px}.grid dd{margin:5px 0 0;font-weight:600}.description{padding-top:14px;border-top:1px solid #e2e8f0;color:#475569}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left}th{background:#f8fafc}.opinion+.opinion{margin-top:15px;padding-top:15px;border-top:1px solid #e2e8f0}.opinion p{margin:6px 0;color:#475569}.files{display:grid;gap:10px}.files article{display:flex;justify-content:space-between;gap:15px;padding:14px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.files small{display:block;margin-top:5px;color:#64748b}.files p{margin:5px 0 0}.files article>div:last-child{display:flex;align-items:center;gap:8px}.files button{padding:7px 10px;border:1px solid #bfdbfe;border-radius:8px;color:#1d4ed8;background:#fff;font-weight:700}.empty{text-align:center;color:#64748b}.timeline{margin:0;padding:0;list-style:none}.timeline li{display:grid;grid-template-columns:18px 1fr;gap:10px;padding-bottom:18px}.timeline li>span{width:11px;height:11px;margin-top:4px;border-radius:50%;background:#2563eb}.timeline time{display:block;margin-top:5px;color:#64748b;font-size:13px}textarea{width:100%;margin-top:10px;padding:11px;border:1px solid #cbd5e1;border-radius:9px;resize:vertical;font:inherit}.feedback{color:#166534}.back-button{padding:10px 18px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;font:inherit;font-weight:700}.actions{display:flex;justify-content:flex-end}@media(max-width:650px){.detail-page{padding:24px 14px}.grid{grid-template-columns:1fr}.files article{flex-direction:column}}
</style>
