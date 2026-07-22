<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { APPLICATION_STATUS, canApplyExtension, canSupplementResult, getApplications } from '../mock/applications.js'

const route = useRoute()
const router = useRouter()
const currentUser = { id: 'stu001', name: '张三', studentId: '2024001' }
const application = computed(() =>
  getApplications().find((item) => item.id === route.params.id && item.currentUserId === currentUser.id),
)

const timeline = computed(() => {
  if (!application.value) return []
  const item = application.value
  const steps = [
    { key: 'student', title: '学生提交申请', state: 'completed', time: item.submitTime, comment: '' },
    getTimelineStep('advisor', '指导老师确认', item),
    getTimelineStep('admin', '管理员受理并分配', item),
    getTimelineStep('reviewer', '审核老师审核', item),
    getTimelineStep('final', '管理员最终确认', item),
  ]
  const supplement = item.timelineEvents?.findLast?.((event) => event.type === 'result_supplemented')
    || [...(item.timelineEvents || [])].reverse().find((event) => event.type === 'result_supplemented')
  if (supplement) steps.splice(1, 0, { key: 'supplement', title: supplement.title, state: 'completed', time: supplement.time, comment: '' })
  const extension = item.timelineEvents?.findLast?.((event) => event.type === 'extension_submitted')
    || [...(item.timelineEvents || [])].reverse().find((event) => event.type === 'extension_submitted')
  if (extension) steps.splice(1, 0, { key: 'extension', title: extension.title, state: 'completed', time: extension.time, comment: '' })
  return steps
})

const result = computed(() => {
  const item = application.value
  if (!item) return null
  const resultMap = {
    advisor_rejected: { title: '指导老师已驳回', reason: item.advisorComment, type: 'rejected' },
    reviewer_rejected: { title: '审核老师已驳回', reason: item.reviewComment, type: 'rejected' },
    final_rejected: { title: '最终驳回', reason: item.finalComment, type: 'rejected' },
    supplement_rejected: { title: '补交成果已驳回', reason: item.supplementAdvisorComment, type: 'rejected' },
    final_approved: { title: '最终通过', reason: `最终认定 ${item.recognizedHours} 小时`, type: 'approved' },
  }
  return resultMap[item.status] ?? null
})

function getTimelineStep(key, title, item) {
  const definitions = {
    advisor: {
      current: APPLICATION_STATUS.PENDING_ADVISOR,
      rejected: APPLICATION_STATUS.ADVISOR_REJECTED,
      completed: item.advisorStatus === 'approved',
      time: item.advisorConfirmTime,
      comment: item.advisorComment,
    },
    admin: {
      current: APPLICATION_STATUS.PENDING_ADMIN_ACCEPT,
      completed: item.adminAcceptStatus === 'accepted',
      time: item.adminAcceptTime,
      comment: item.adminAcceptComment,
    },
    reviewer: {
      current: APPLICATION_STATUS.PENDING_REVIEWER,
      rejected: APPLICATION_STATUS.REVIEWER_REJECTED,
      completed: ['approved', 'modified_approved'].includes(item.reviewStatus),
      time: item.reviewTime,
      comment: item.reviewComment,
    },
    final: {
      current: APPLICATION_STATUS.PENDING_ADMIN_FINAL,
      rejected: APPLICATION_STATUS.FINAL_REJECTED,
      completed: item.finalStatus === 'approved',
      time: item.finalConfirmTime,
      comment: item.finalComment,
    },
  }
  const definition = definitions[key]
  let state = 'pending'
  if (item.status === definition.rejected) state = 'rejected'
  else if (definition.completed) state = 'completed'
  else if (item.status === definition.current) state = 'current'
  return { key, title, state, time: definition.time, comment: definition.comment }
}

function preview(file) {
  window.alert(`正在预览：${file.name}`)
}

function download(file) {
  window.alert(`正在下载：${file.name}`)
}

function goBack() {
  router.push('/student/hour-progress')
}
</script>

<template>
  <main class="detail-page">
    <div class="page-content">
      <template v-if="application">
        <header class="page-header">
          <div>
            <p class="eyebrow">APPLICATION PROGRESS DETAIL</p>
            <h1>{{ application.title }}</h1>
            <p>{{ application.id }}</p>
          </div>
          <StatusTag :status="application.status" />
        </header>

        <section v-if="result" class="result-banner" :class="`result-banner--${result.type}`">
          <strong>{{ result.title }}</strong>
          <p>{{ result.reason || '暂无处理意见' }}</p>
        </section>

        <section class="card">
          <h2>流程进度</h2>
          <ol class="timeline">
            <li v-for="step in timeline" :key="step.key" :class="`timeline-step--${step.state}`">
              <span class="timeline-dot" aria-hidden="true"></span>
              <div>
                <div class="timeline-title">
                  <strong>{{ step.title }}</strong>
                  <span>{{ { completed: '已完成', current: '进行中', pending: '待处理', rejected: '已驳回' }[step.state] }}</span>
                </div>
                <time v-if="step.time">{{ step.time }}</time>
                <p v-if="step.state === 'rejected'">驳回原因：{{ step.comment || '未填写' }}</p>
              </div>
            </li>
          </ol>
        </section>

        <section class="card">
          <h2>学生提交信息</h2>
          <dl class="info-grid">
            <div><dt>申请标题</dt><dd>{{ application.title }}</dd></div>
            <div><dt>申请来源</dt><dd>{{ application.sourceText }}</dd></div>
            <div><dt>申请类型</dt><dd>{{ application.applyTypeText }}</dd></div>
            <div><dt>申请课时数</dt><dd>{{ application.requestedHours }} 小时</dd></div>
            <div><dt>提交时间</dt><dd>{{ application.submitTime }}</dd></div>
            <div><dt>队长</dt><dd>{{ application.members.find((member) => member.id === application.captainId)?.name || '--' }}</dd></div>
          </dl>
          <div class="table-wrapper">
            <table>
              <thead><tr><th>成员姓名</th><th>学号</th><th>学院</th><th>专业</th><th>角色</th></tr></thead>
              <tbody><tr v-for="member in application.members" :key="member.id"><td>{{ member.name }}</td><td>{{ member.studentId }}</td><td>{{ member.college || '--' }}</td><td>{{ member.major || '--' }}</td><td>{{ member.role === 'captain' ? '队长' : '成员' }}</td></tr></tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>指导老师确认</h2>
          <dl class="info-grid">
            <div><dt>主指导老师</dt><dd>{{ application.mainAdvisor?.name || '--' }}</dd></div>
            <div><dt>查看导师</dt><dd>{{ application.viewAdvisors.map((advisor) => advisor.name).join('、') || '--' }}</dd></div>
            <div><dt>确认状态</dt><dd><StatusTag :status="application.advisorStatus" :text="{ pending: '待确认', approved: '已确认', rejected: '已驳回' }[application.advisorStatus]" /></dd></div>
            <div><dt>确认时间</dt><dd>{{ application.advisorConfirmTime || '--' }}</dd></div>
          </dl>
          <p class="opinion">确认意见：{{ application.advisorComment || '暂无' }}</p>
        </section>

        <section class="card">
          <h2>管理员受理与分配</h2>
          <dl class="info-grid">
            <div><dt>受理状态</dt><dd><StatusTag :status="application.adminAcceptStatus" :text="{ pending: '待受理并分配', accepted: '已受理并分配' }[application.adminAcceptStatus]" /></dd></div>
            <div><dt>受理时间</dt><dd>{{ application.adminAcceptTime || '--' }}</dd></div>
            <div><dt>分配审核老师</dt><dd>{{ application.reviewer?.name || '待分配' }}</dd></div>
            <div><dt>审核方向</dt><dd>{{ application.reviewer?.direction || '--' }}</dd></div>
          </dl>
          <p class="opinion">受理意见：{{ application.adminAcceptComment || '暂无' }}</p>
        </section>

        <section class="card">
          <h2>审核老师审核</h2>
          <dl class="info-grid">
            <div><dt>审核老师</dt><dd>{{ application.reviewer?.name || '--' }}</dd></div>
            <div><dt>审核结果</dt><dd><StatusTag :status="application.reviewStatus" :text="{ pending: '待审核', approved: '审核通过', modified_approved: '修改课时后审核通过', rejected: '已驳回' }[application.reviewStatus]" /></dd></div>
            <div><dt>原申请课时</dt><dd>{{ application.originalHours ?? application.requestedHours }} 小时</dd></div>
            <div><dt>审核认定课时</dt><dd>{{ application.recognizedHours ?? '--' }}<template v-if="application.recognizedHours !== null"> 小时</template></dd></div>
            <div><dt>审核时间</dt><dd>{{ application.reviewTime || '--' }}</dd></div>
          </dl>
          <p class="opinion">审核意见：{{ application.reviewComment || '暂无' }}</p>
        </section>

        <section class="card">
          <h2>管理员最终确认</h2>
          <dl class="info-grid">
            <div><dt>最终确认状态</dt><dd><StatusTag :status="application.finalStatus" :text="{ pending: '待最终确认', approved: '最终通过', rejected: '最终驳回' }[application.finalStatus]" /></dd></div>
            <div><dt>最终确认时间</dt><dd>{{ application.finalConfirmTime || '--' }}</dd></div>
            <div><dt>最终认定课时</dt><dd>{{ application.status === APPLICATION_STATUS.FINAL_APPROVED ? `${application.recognizedHours} 小时` : '--' }}</dd></div>
          </dl>
          <p class="opinion">最终确认意见：{{ application.finalComment || '暂无' }}</p>
        </section>

        <section class="card">
          <h2>学生上传材料</h2>
          <div v-if="application.attachments.length" class="file-list">
            <article v-for="file in application.attachments" :key="file.id">
              <div><strong>{{ file.name }}</strong><small>{{ file.type }} · {{ file.uploadedAt || 'Mock 上传时间' }}</small></div>
              <div><button type="button" @click="preview(file)">预览</button><button type="button" @click="download(file)">下载</button></div>
            </article>
          </div>
          <p v-else class="empty">暂无上传材料</p>
        </section>

        <section v-if="canSupplementResult(application) || canApplyExtension(application)" class="card"><h2>待补交成果</h2><p class="opinion">请在预计成果提交时间前补交成果；如无法按时提交，可申请延期。</p></section>
        <div class="actions"><RouterLink v-if="canSupplementResult(application)" :to="`/student/hour-progress/${application.id}/supplement-result`">补交成果</RouterLink><RouterLink v-if="canApplyExtension(application)" :to="`/student/hour-progress/${application.id}/extension`">申请延期</RouterLink><button type="button" @click="goBack">返回申请列表</button></div>
      </template>
      <section v-else class="card empty"><h1>未找到申请</h1><p>该申请不存在，或不属于当前学生。</p><button type="button" @click="goBack">返回申请列表</button></section>
    </div>
  </main>
</template>

<style scoped>
.detail-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.page-content{width:min(100%,980px);margin:0 auto}.page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:20px}.page-header h1{margin:0 0 8px;font-size:29px}.page-header p{margin:0;color:#64748b}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px;font-size:19px}.result-banner{margin-bottom:18px;padding:16px 18px;border:1px solid;border-radius:12px}.result-banner strong{font-size:17px}.result-banner p{margin:5px 0 0}.result-banner--approved{color:#166534;border-color:#bbf7d0;background:#f0fdf4}.result-banner--rejected{color:#b91c1c;border-color:#fecaca;background:#fef2f2}.info-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:0}.info-grid dt{color:#64748b;font-size:13px}.info-grid dd{margin:5px 0 0;font-weight:600}.opinion{margin:18px 0 0;padding-top:14px;border-top:1px solid #e2e8f0;color:#475569;line-height:1.7}.table-wrapper{overflow-x:auto;margin-top:20px}table{width:100%;border-collapse:collapse}th,td{padding:11px 12px;border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{color:#475569;background:#f8fafc;font-size:13px}.timeline{margin:0;padding:0;list-style:none}.timeline li{position:relative;display:grid;grid-template-columns:22px 1fr;gap:12px;padding-bottom:22px}.timeline li:not(:last-child)::before{position:absolute;top:15px;bottom:0;left:6px;width:2px;background:#e2e8f0;content:''}.timeline-dot{z-index:1;width:14px;height:14px;margin-top:3px;border:3px solid #cbd5e1;border-radius:50%;background:#fff}.timeline-title{display:flex;align-items:center;justify-content:space-between;gap:16px}.timeline-title span,.timeline time{color:#64748b;font-size:13px}.timeline time{display:block;margin-top:5px}.timeline li p{margin:7px 0 0;color:#b91c1c}.timeline-step--completed .timeline-dot{border-color:#22c55e;background:#22c55e}.timeline-step--current .timeline-dot{border-color:#2563eb;background:#dbeafe}.timeline-step--rejected .timeline-dot{border-color:#ef4444;background:#ef4444}.timeline-step--completed .timeline-title span{color:#166534}.timeline-step--current .timeline-title span{color:#1d4ed8}.timeline-step--rejected .timeline-title span{color:#b91c1c}.file-list{display:grid;gap:10px}.file-list article{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}.file-list small{display:block;margin-top:5px;color:#64748b}.file-list article>div:last-child{display:flex;gap:8px}.file-list button,.actions button,.empty button{padding:8px 12px;border:1px solid #bfdbfe;border-radius:8px;color:#1d4ed8;background:#fff;font:inherit;font-weight:700;cursor:pointer}.actions{display:flex;justify-content:flex-end}.actions button,.empty button{padding:10px 18px;border-color:#cbd5e1;color:#334155}.empty{text-align:center;color:#64748b}@media(max-width:680px){.detail-page{padding:24px 14px}.page-header{flex-direction:column}.info-grid{grid-template-columns:1fr}.file-list article{align-items:flex-start;flex-direction:column}.timeline-title{align-items:flex-start;flex-direction:column;gap:4px}}
</style>
