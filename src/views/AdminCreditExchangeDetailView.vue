<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { EXCHANGE_STATUS, finalApproveExchange, finalRejectExchange, getExchangeFinalApproveFailure, getExchanges, PENDING_CREDIT_STATUSES } from '../mock/exchanges.js'

const route = useRoute()
const router = useRouter()
const opinion = ref('')
const item = computed(() => getExchanges().find((exchange) => exchange.id === route.params.id || exchange.exchangeId === route.params.id))
const canHandle = computed(() => PENDING_CREDIT_STATUSES.includes(item.value?.status))
const allocatedHoursTotal = computed(() => (item.value?.memberDistributions || []).reduce((sum, member) => sum + Number(member.allocatedHours || 0), 0))
const allocatedCreditsTotal = computed(() => (item.value?.memberDistributions || []).reduce((sum, member) => sum + Number(member.allocatedCredits || 0), 0))

function approve() {
  const failure = getExchangeFinalApproveFailure(item.value)
  if (failure) return window.alert(failure)
  const approved = finalApproveExchange(item.value.id, opinion.value.trim())
  if (!approved) return window.alert('当前申请不满足最终确认兑换条件。')
  window.alert('最终确认兑换成功，学生获得对应学分。')
  goBack()
}
function reject() {
  if (!opinion.value.trim()) return window.alert('驳回兑换必须填写处理意见。')
  if (!item.value || !finalRejectExchange(item.value.id, opinion.value.trim())) return window.alert('当前申请不可驳回。')
  window.alert('已驳回兑换申请。')
  goBack()
}
function fileAction(action, file) { window.alert(`${action}“${file.name}”仅为 Mock 演示，暂未接入真实文件服务。`) }
function goBack() { router.push('/admin/final-confirm/exchanges') }
</script>

<template>
  <main class="detail-page"><div class="content">
    <template v-if="item">
      <header class="page-header"><div><p class="eyebrow">A502 · EXCHANGE FINAL CONFIRMATION</p><h1>兑换最终确认详情</h1><p>{{ item.exchangeId }} · {{ item.projectTitle }}</p></div><StatusTag :status="item.status" :text="canHandle ? '待管理员最终确认' : ''" /></header>
      <section class="card"><h2>申请人信息</h2><dl class="grid"><div><dt>学生姓名</dt><dd>{{ item.studentName }}</dd></div><div><dt>学号</dt><dd>{{ item.studentId }}</dd></div><div><dt>确认类型</dt><dd>学分兑换最终确认</dd></div><div><dt>提交时间</dt><dd>{{ item.submitTime }}</dd></div></dl></section>
      <section class="card"><h2>团队与任务信息</h2><dl class="grid"><div><dt>团队名称</dt><dd>{{ item.teamName || '--' }}</dd></div><div><dt>任务名称</dt><dd>{{ item.taskName || item.projectTitle }}</dd></div><div><dt>已到账课时</dt><dd>{{ item.finalHours }} 课时 · {{ item.hoursArrived ? '已到账' : '未到账' }}</dd></div><div><dt>是否已兑换</dt><dd>{{ item.exchanged ? '已兑换' : '未兑换' }}</dd></div><div><dt>申请兑换课时</dt><dd>{{ item.exchangeHours }}</dd></div><div><dt>申请兑换学分</dt><dd>{{ Number(item.estimatedCredits || 0).toFixed(2) }}</dd></div></dl></section>
      <section class="card"><h2>成员学时 / 学分分配表</h2><div class="table-wrap"><table><thead><tr><th>成员姓名</th><th>学号</th><th>成员角色</th><th>分配课时</th><th>分配学分</th><th>备注</th></tr></thead><tbody><tr v-for="member in item.memberDistributions" :key="member.studentId"><td>{{ member.studentName }}</td><td>{{ member.studentId }}</td><td>{{ member.role === 'captain' ? '队长' : '成员' }}</td><td>{{ member.allocatedHours }}</td><td>{{ Number(member.allocatedCredits || 0).toFixed(2) }}</td><td>{{ member.remark || '--' }}</td></tr><tr v-if="!item.memberDistributions?.length"><td class="empty" colspan="6">暂无成员分配数据。</td></tr></tbody></table></div><dl class="grid allocation-summary"><div><dt>项目最终认定课时</dt><dd>{{ item.finalHours }}</dd></div><div><dt>成员分配课时总和</dt><dd>{{ allocatedHoursTotal }}</dd></div><div><dt>项目预计总学分</dt><dd>{{ Number(item.estimatedCredits || 0).toFixed(2) }}</dd></div><div><dt>成员分配学分总和</dt><dd>{{ allocatedCreditsTotal.toFixed(2) }}</dd></div></dl></section>
      <section class="card"><h2>指导老师确认</h2><dl class="grid"><div><dt>确认状态</dt><dd><StatusTag :status="item.advisorConfirmStatus" /></dd></div><div><dt>确认意见</dt><dd>{{ item.advisorComment || '无' }}</dd></div></dl></section>
      <section class="card"><h2>分配证明材料</h2><div class="files"><article v-for="file in item.proofMaterials" :key="file.id || file.name"><div><strong>{{ file.name }}</strong><small>{{ file.type || '未知类型' }} · {{ file.uploadedAt || '--' }}</small></div><div><button @click="fileAction('预览', file)">预览</button><button @click="fileAction('下载', file)">下载</button></div></article><p v-if="!item.proofMaterials?.length" class="empty">暂无证明材料。</p></div></section>
      <section class="card"><h2>最终确认处理</h2><dl class="grid summary"><div><dt>当前最终确认状态</dt><dd><StatusTag :status="item.status" /></dd></div><div><dt>最终确认时间</dt><dd>{{ item.finalConfirmTime || '--' }}</dd></div></dl><label for="opinion"><strong>处理意见</strong></label><textarea id="opinion" v-model="opinion" rows="5" placeholder="最终确认意见可选；驳回兑换时必填。"></textarea></section>
      <div class="actions"><button class="back" type="button" @click="goBack">返回</button><template v-if="canHandle"><button class="reject" type="button" @click="reject">驳回兑换</button><button class="approve" type="button" @click="approve">最终确认兑换</button></template></div>
    </template>
    <section v-else class="card empty"><h1>未找到兑换申请</h1><button class="back" @click="goBack">返回</button></section>
  </div></main>
</template>

<style scoped>
.detail-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,980px);margin:auto}.page-header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}.page-header h1{margin:0}.page-header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800;letter-spacing:.12em}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px;font-size:19px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.grid dt{color:#64748b;font-size:13px}.grid dd{margin:5px 0 0;font-weight:600}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc}.files{display:grid;gap:10px}.files article{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:14px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.files small{display:block;margin-top:5px;color:#64748b}.files article>div:last-child{display:flex;gap:8px}.files button{padding:7px 10px;border:1px solid #bfdbfe;border-radius:8px;color:#1d4ed8;background:#fff;font-weight:700;cursor:pointer}.summary{margin-bottom:18px}textarea{width:100%;margin-top:10px;padding:11px;border:1px solid #cbd5e1;border-radius:9px;resize:vertical;font:inherit}.actions{display:flex;justify-content:flex-end;gap:10px}.actions button,.empty button{padding:10px 18px;border-radius:9px;font:inherit;font-weight:700;cursor:pointer}.back{border:1px solid #cbd5e1;background:#fff}.reject{border:0;color:#fff;background:#dc2626}.approve{border:0;color:#fff;background:#2563eb}.empty{text-align:center;color:#64748b}@media(max-width:650px){.detail-page{padding:24px 14px}.page-header{flex-direction:column}.grid{grid-template-columns:1fr}.files article{align-items:flex-start;flex-direction:column}.actions{flex-wrap:wrap}}
.allocation-summary{margin-top:18px;padding-top:18px;border-top:1px solid #e2e8f0}
</style>
