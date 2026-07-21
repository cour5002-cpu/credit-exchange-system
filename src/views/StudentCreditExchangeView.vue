<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AttachmentNotice from '../components/AttachmentNotice.vue'
import StatusTag from '../components/StatusTag.vue'
import { APPLICATION_STATUS, getApplications } from '../mock/applications.js'
import { addExchange, EXCHANGE_STATUS } from '../mock/exchanges.js'

const router = useRouter()
const currentUser = { id: 'stu001', name: '张三', studentId: '2024001' }
const hoursPerCredit = 8
const form = reactive({ applicationId: '', applyReason: '', attachment: null })
const feedback = ref({ type: '', message: '' })
const attachmentInput = ref(null)

const eligibleApplications = computed(() =>
  getApplications().filter((application) =>
    application.currentUserId === currentUser.id
    && application.status === APPLICATION_STATUS.FINAL_APPROVED,
  ),
)
const selectedApplication = computed(() =>
  eligibleApplications.value.find((application) => application.id === form.applicationId) ?? null,
)
const finalHours = computed(() => {
  if (!selectedApplication.value) return 0
  return Number(selectedApplication.value.recognizedHours ?? selectedApplication.value.requestedHours) || 0
})
const estimatedCredits = computed(() =>
  finalHours.value > 0 ? (finalHours.value / hoursPerCredit).toFixed(2) : '0.00',
)

function validateForm() {
  if (!form.applicationId) return '请选择已最终确认通过的项目'
  if (!selectedApplication.value || selectedApplication.value.status !== APPLICATION_STATUS.FINAL_APPROVED) {
    return '只有最终确认通过的项目才能申请学分兑换'
  }
  if (finalHours.value <= 0) return '该项目暂无可兑换课时'
  if (!form.attachment) return '请上传认定证明'
  return ''
}

function handleAttachmentChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  form.attachment = {
    id: `EX-ATT-${Date.now()}`,
    name: file.name,
    type: file.type || '未知类型',
    size: file.size,
    uploadedAt: new Date().toLocaleString('zh-CN', { hour12: false }),
  }
  feedback.value = { type: '', message: '' }
}

function removeAttachment() {
  form.attachment = null
  if (attachmentInput.value) attachmentInput.value.value = ''
}

function createExchange(status) {
  const application = selectedApplication.value
  return addExchange({
    applicationId: application?.id ?? '',
    projectTitle: application?.title ?? '',
    studentName: currentUser.name,
    studentId: currentUser.studentId,
    currentUserId: currentUser.id,
    source: application?.source ?? '',
    sourceText: application?.sourceText ?? '',
    teamName: application?.taskTitle ? `${application.taskTitle}团队` : `${currentUser.name}团队`,
    taskName: application?.taskTitle || application?.title || '',
    hoursArrived: true,
    exchanged: false,
    advisorConfirmStatus: application?.advisorStatus || 'approved',
    advisorComment: application?.advisorComment || '',
    finalHours: finalHours.value,
    exchangeHours: finalHours.value,
    estimatedCredits: Number(estimatedCredits.value),
    creditRule: { hoursPerCredit, text: `每 ${hoursPerCredit} 课时兑换 1 学分` },
    proofMaterials: form.attachment ? [{ ...form.attachment }] : [],
    memberDistributions: (application?.members?.length ? application.members : [{ ...currentUser, role: 'captain' }]).map((member) => ({
      id: member.id,
      name: member.name,
      studentId: member.studentId,
      isCaptain: member.role === 'captain',
      allocatedHours: member.id === currentUser.id ? finalHours.value : 0,
      allocatedCredits: member.id === currentUser.id ? Number(estimatedCredits.value) : 0,
      description: member.id === currentUser.id ? '本次兑换申请人' : '本次未分配兑换学分',
      confirmStatus: member.id === currentUser.id ? 'confirmed' : 'pending',
    })),
    applyReason: form.applyReason.trim(),
    status,
  })
}

function saveDraft() {
  createExchange('draft')
  feedback.value = { type: 'success', message: '学分兑换申请草稿已模拟保存。' }
  window.alert(feedback.value.message)
}

function submitExchange() {
  const error = validateForm()
  if (error) {
    feedback.value = { type: 'error', message: error }
    window.alert(error)
    return
  }
  createExchange(EXCHANGE_STATUS.PENDING_CONFIRMATION)
  feedback.value = { type: 'success', message: '学分兑换申请提交成功，已进入确认流程。' }
  window.alert(feedback.value.message)
}

function goBack() {
  router.push('/student/dashboard')
}
</script>

<template>
  <main class="exchange-page">
    <div class="page-content">
      <header class="page-header">
        <div><p class="eyebrow">CREDIT EXCHANGE</p><h1>学分兑换申请</h1><p>选择已经最终确认通过的项目，申请兑换实践学分。</p></div>
        <button class="secondary-button" type="button" @click="goBack">返回学生首页</button>
      </header>

      <section class="summary-grid" aria-label="兑换概览">
        <article><span>可兑换项目</span><strong>{{ eligibleApplications.length }}</strong><small>个最终通过项目</small></article>
        <article><span>项目最终认定课时</span><strong>{{ finalHours }}</strong><small>小时，由系统自动读取</small></article>
        <article><span>本次预计兑换学分</span><strong>{{ estimatedCredits }}</strong><small>每 {{ hoursPerCredit }} 课时兑换 1 学分</small></article>
      </section>

      <form class="exchange-form" novalidate @submit.prevent="submitExchange">
        <section class="form-card">
          <div class="section-heading"><div><h2>学生信息</h2><p>兑换申请将以当前登录学生身份提交。</p></div><StatusTag status="draft" text="填写中" /></div>
          <div class="form-grid">
            <div class="form-field"><label for="student-name">学生姓名</label><input id="student-name" :value="currentUser.name" readonly /></div>
            <div class="form-field"><label for="student-id">学号</label><input id="student-id" :value="currentUser.studentId" readonly /></div>
          </div>
        </section>

        <section class="form-card">
          <div class="section-heading"><div><h2>选择可兑换项目</h2><p>仅展示你提交且已最终确认通过的课时申请。</p></div></div>
          <div class="form-field">
            <label for="exchange-project">可兑换项目 <span>*</span></label>
            <select id="exchange-project" v-model="form.applicationId">
              <option value="">请选择已最终确认通过的项目</option>
              <option v-for="application in eligibleApplications" :key="application.id" :value="application.id">
                {{ application.title }} · 最终认定 {{ application.recognizedHours }} 小时
              </option>
            </select>
          </div>
          <p v-if="!eligibleApplications.length" class="empty-state">暂无可兑换项目，请等待课时申请完成最终确认。</p>
        </section>

        <section v-if="selectedApplication" class="form-card">
          <div class="section-heading"><div><h2>项目认定信息</h2><p>{{ selectedApplication.id }}</p></div><StatusTag :status="selectedApplication.status" /></div>
          <dl class="info-grid">
            <div><dt>项目名称 / 申请标题</dt><dd>{{ selectedApplication.title }}</dd></div>
            <div><dt>申请来源</dt><dd>{{ selectedApplication.sourceText }}</dd></div>
            <div><dt>原申请课时</dt><dd>{{ selectedApplication.originalHours ?? selectedApplication.requestedHours }} 小时</dd></div>
            <div><dt>审核认定课时</dt><dd>{{ selectedApplication.recognizedHours }} 小时</dd></div>
            <div><dt>最终认定课时</dt><dd>{{ finalHours }} 小时</dd></div>
            <div><dt>审核老师</dt><dd>{{ selectedApplication.reviewer?.name || '--' }}</dd></div>
            <div><dt>最终确认时间</dt><dd>{{ selectedApplication.finalConfirmTime || '--' }}</dd></div>
          </dl>
        </section>

        <section class="form-card">
          <div class="section-heading"><div><h2>自动兑换信息</h2><p>兑换课时和预计学分由系统自动计算。</p></div></div>
          <div class="form-grid">
            <div class="form-field"><label for="exchange-hours">兑换课时数</label><input id="exchange-hours" :value="finalHours" type="number" readonly /><small>兑换课时数由已最终确认的项目课时自动生成，学生不可手动修改。</small></div>
            <div class="form-field"><label for="estimated-credits">预计兑换学分</label><input id="estimated-credits" :value="estimatedCredits" readonly /><small>兑换规则：每 {{ hoursPerCredit }} 课时兑换 1 学分，保留 2 位小数。</small></div>
            <div class="form-field form-field--wide"><label for="apply-reason">申请说明</label><textarea id="apply-reason" v-model="form.applyReason" rows="5" placeholder="可填写兑换用途或需要说明的情况。"></textarea></div>
          </div>
        </section>

        <section class="form-card">
          <div class="section-heading"><div><h2>上传认定证明</h2><p>当前为 Mock 文件选择，不会上传到服务器。</p></div></div>
          <AttachmentNotice title="认定证明上传说明" description="请上传课时最终认定证明、最终确认结果截图或其他辅助材料，用于管理员核对兑换资格。" :required="true" :accept-types="['PDF', 'Word', '图片']" />
          <label class="upload-control"><span>选择认定证明 <strong>*</strong></span><input ref="attachmentInput" type="file" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" @change="handleAttachmentChange" /></label>
          <article v-if="form.attachment" class="selected-file"><div><strong>{{ form.attachment.name }}</strong><small>{{ form.attachment.type }} · {{ form.attachment.uploadedAt }}</small></div><button type="button" @click="removeAttachment">移除</button></article>
        </section>

        <p v-if="feedback.message" class="feedback" :class="`feedback--${feedback.type}`" role="status">{{ feedback.message }}</p>
        <div class="form-actions"><button class="secondary-button" type="button" @click="goBack">返回</button><button class="secondary-button" type="button" @click="saveDraft">保存草稿</button><button class="primary-button" type="submit">提交兑换申请</button></div>
      </form>
    </div>
  </main>
</template>

<style scoped>
.exchange-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.page-content{width:min(100%,1020px);margin:0 auto}.page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:24px}.page-header h1{margin:0 0 8px;font-size:30px}.page-header p{color:#64748b}.summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-bottom:22px}.summary-grid article{padding:20px;border:1px solid #dbeafe;border-radius:14px;background:#fff}.summary-grid span,.summary-grid small{display:block;color:#64748b}.summary-grid strong{display:inline-block;margin:9px 5px 3px 0;color:#1d4ed8;font-size:30px}.summary-grid small{font-size:13px}.exchange-form{display:grid;gap:20px}.form-card{padding:24px;border:1px solid #e2e8f0;border-radius:16px;background:#fff;box-shadow:0 8px 24px rgba(15,23,42,.04)}.section-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:20px}.section-heading h2{margin:0 0 6px;font-size:20px}.section-heading p{margin:0;color:#64748b;font-size:14px}.form-grid,.info-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.form-field--wide{grid-column:1/-1}.form-field label,.upload-control>span{display:block;margin-bottom:8px;color:#334155;font-weight:700}.form-field label span,.upload-control strong{color:#dc2626}.form-field input,.form-field select,.form-field textarea,.upload-control input{width:100%;padding:11px 12px;border:1px solid #cbd5e1;border-radius:9px;background:#fff;font:inherit}.form-field input[readonly]{color:#475569;background:#f8fafc}.form-field textarea{resize:vertical}.form-field small{display:block;margin-top:7px;color:#64748b;line-height:1.5}.info-grid{margin:0}.info-grid dt{color:#64748b;font-size:13px}.info-grid dd{margin:5px 0 0;font-weight:600}.empty-state{margin:14px 0 0;padding:18px;border-radius:10px;color:#64748b;background:#f8fafc;text-align:center}.upload-control{display:block;margin-top:18px}.upload-control input{padding:9px}.selected-file{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:12px;padding:14px;border:1px solid #bfdbfe;border-radius:10px;background:#eff6ff}.selected-file small{display:block;margin-top:4px;color:#64748b}.selected-file button{padding:7px 11px;border:1px solid #fecaca;border-radius:8px;color:#b91c1c;background:#fff;font:inherit;font-weight:700;cursor:pointer}.feedback{margin:0;padding:12px 16px;border-radius:10px}.feedback--error{color:#b91c1c;background:#fef2f2}.feedback--success{color:#166534;background:#f0fdf4}.form-actions{display:flex;justify-content:flex-end;gap:12px}@media(max-width:700px){.exchange-page{padding:24px 14px}.page-header,.section-heading{flex-direction:column}.summary-grid,.form-grid,.info-grid{grid-template-columns:1fr}.form-field--wide{grid-column:auto}.form-actions{flex-wrap:wrap}}
</style>
