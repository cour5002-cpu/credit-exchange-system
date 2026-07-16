<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AttachmentNotice from '../components/AttachmentNotice.vue'
import ReviewActionBar from '../components/ReviewActionBar.vue'
import StatusTag from '../components/StatusTag.vue'
import { getConfirmationTypeText, getTeacherConfirmation } from '../mock/teacherConfirmations'

const route = useRoute()
const router = useRouter()
const confirmation = computed(() => getTeacherConfirmation(route.params.id))
const opinion = ref('')
const feedback = ref({ type: '', message: '' })

function approveConfirmation() {
  if (!confirmation.value) return
  confirmation.value.status = 'confirmed'
  feedback.value = { type: 'success', message: '确认通过成功' }
  window.alert(feedback.value.message)
}

function rejectConfirmation() {
  if (!opinion.value.trim()) {
    feedback.value = { type: 'error', message: '请填写驳回原因' }
    window.alert(feedback.value.message)
    return
  }
  confirmation.value.status = 'rejected'
  feedback.value = { type: 'success', message: '驳回成功' }
  window.alert(feedback.value.message)
}

function goBack() {
  router.push('/teacher/confirm')
}

function previewAttachment(file) {
  window.alert(`正在预览：${file.name}`)
}

function downloadAttachment(file) {
  window.alert(`正在下载：${file.name}`)
}
</script>

<template>
  <main class="detail-page">
    <div class="detail-content">
      <template v-if="confirmation">
        <header class="page-header">
          <div><p class="eyebrow">CONFIRMATION DETAIL</p><h1>{{ confirmation.title }}</h1><p>{{ getConfirmationTypeText(confirmation.type) }}</p></div>
          <StatusTag :status="confirmation.status" />
        </header>

        <section class="detail-card">
          <h2>学生信息</h2>
          <dl class="info-grid">
            <div><dt>姓名</dt><dd>{{ confirmation.student.name }}</dd></div>
            <div><dt>学号</dt><dd>{{ confirmation.student.studentNo }}</dd></div>
            <div><dt>学院</dt><dd>{{ confirmation.student.college }}</dd></div>
            <div><dt>专业</dt><dd>{{ confirmation.student.major }}</dd></div>
          </dl>
        </section>

        <section class="detail-card">
          <h2>申请信息</h2>
          <dl class="info-grid">
            <div><dt>事项编号</dt><dd>{{ confirmation.id }}</dd></div>
            <div><dt>申请来源</dt><dd>{{ confirmation.application.source }}</dd></div>
            <div><dt>申请类别</dt><dd>{{ confirmation.application.category }}</dd></div>
            <div><dt>申请课时</dt><dd>{{ confirmation.application.requestedHours }} 小时</dd></div>
            <div v-if="confirmation.application.requestedCredits"><dt>兑换学分</dt><dd>{{ confirmation.application.requestedCredits }} 学分</dd></div>
            <div><dt>提交时间</dt><dd>{{ confirmation.submittedAt }}</dd></div>
          </dl>
        </section>

        <section class="detail-card">
          <h2>团队成员</h2>
          <div class="table-wrapper"><table><thead><tr><th>姓名</th><th>学号</th><th>学院</th><th>专业</th><th>角色</th></tr></thead><tbody><tr v-for="member in confirmation.members" :key="member.studentNo"><td>{{ member.name }}</td><td>{{ member.studentNo }}</td><td>{{ member.college }}</td><td>{{ member.major }}</td><td>{{ member.isLeader ? '队长' : '成员' }}</td></tr></tbody></table></div>
        </section>

        <section class="detail-card">
          <h2>主指导老师</h2>
          <p>{{ confirmation.primaryTeacher.name }} · {{ confirmation.primaryTeacher.department }}</p>
        </section>

        <section class="detail-card">
          <h2>成果或申请说明</h2>
          <p class="description">{{ confirmation.description }}</p>
          <AttachmentNotice title="附件材料摘要" :description="confirmation.attachment" :required="false" :accept-types="['PDF', 'Word', '图片']" />
        </section>

        <section class="detail-card" aria-labelledby="student-attachments-title">
          <h2 id="student-attachments-title">学生上传材料</h2>
          <div v-if="confirmation.attachments?.length" class="attachment-list">
            <article v-for="file in confirmation.attachments" :key="file.id" class="attachment-item">
              <div class="attachment-icon" aria-hidden="true">文</div>
              <div class="attachment-info">
                <h3>{{ file.name }}</h3>
                <div class="attachment-meta">
                  <span>{{ file.type }}</span>
                  <span>上传时间：{{ file.uploadedAt }}</span>
                </div>
                <p>{{ file.description }}</p>
              </div>
              <div class="attachment-actions">
                <button type="button" @click="previewAttachment(file)">预览</button>
                <button type="button" @click="downloadAttachment(file)">下载</button>
              </div>
            </article>
          </div>
          <p v-else class="attachment-empty">暂无上传材料</p>
        </section>

        <section class="detail-card">
          <label for="confirmation-opinion"><strong>指导老师确认意见</strong></label>
          <textarea id="confirmation-opinion" v-model="opinion" rows="5" placeholder="请输入确认意见；驳回时必须填写驳回原因。"></textarea>
          <p v-if="feedback.message" class="feedback" :class="`feedback--${feedback.type}`" role="status">{{ feedback.message }}</p>
        </section>

        <ReviewActionBar approve-text="确认通过" reject-text="驳回" @approve="approveConfirmation" @reject="rejectConfirmation">
          <template #before><button class="back-button" type="button" @click="goBack">返回</button></template>
        </ReviewActionBar>
      </template>

      <section v-else class="not-found"><h1>未找到确认事项</h1><p>该事项可能不存在或已被移除。</p><button class="back-button" type="button" @click="goBack">返回待确认事项</button></section>
    </div>
  </main>
</template>

<style scoped>
.detail-page { min-height: 100vh; padding: 40px 24px; background: #f3f6fb; }.detail-content { width: min(100%, 960px); margin: 0 auto; }.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 22px; }.page-header h1 { margin: 0 0 8px; font-size: 29px; }.page-header p { margin: 0; color: #64748b; }.detail-card { margin-bottom: 18px; padding: 22px; border: 1px solid #e2e8f0; border-radius: 14px; background: #fff; }.detail-card h2 { margin: 0 0 18px; font-size: 19px; }.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; margin: 0; }.info-grid dt { margin-bottom: 5px; color: #64748b; font-size: 13px; }.info-grid dd { margin: 0; color: #1e293b; font-weight: 600; }.description { color: #475569; line-height: 1.75; }.table-wrapper { overflow-x: auto; }table { width: 100%; border-collapse: collapse; }th, td { padding: 11px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; }th { color: #475569; background: #f8fafc; font-size: 13px; }textarea { width: 100%; margin-top: 10px; padding: 11px 12px; border: 1px solid #cbd5e1; border-radius: 9px; resize: vertical; font: inherit; }.feedback { margin: 12px 0 0; padding: 10px 12px; border-radius: 8px; }.feedback--error { color: #b91c1c; background: #fef2f2; }.feedback--success { color: #166534; background: #f0fdf4; }.back-button { padding: 10px 18px; border: 1px solid #cbd5e1; border-radius: 10px; color: #334155; background: #fff; font: inherit; font-weight: 700; cursor: pointer; }.not-found { padding: 40px; border-radius: 14px; background: #fff; text-align: center; }
.attachment-list { display: grid; gap: 12px; }.attachment-item { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 14px; padding: 15px; border: 1px solid #e2e8f0; border-radius: 10px; background: #f8fafc; }.attachment-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 9px; color: #1d4ed8; background: #dbeafe; font-weight: 800; }.attachment-info h3 { margin: 0; color: #1e293b; font-size: 15px; }.attachment-meta { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 5px; color: #64748b; font-size: 12px; }.attachment-info p { margin: 6px 0 0; color: #475569; font-size: 13px; }.attachment-actions { display: flex; gap: 8px; }.attachment-actions button { padding: 7px 11px; border: 1px solid #bfdbfe; border-radius: 8px; color: #1d4ed8; background: #fff; font: inherit; font-weight: 700; cursor: pointer; }.attachment-empty { margin: 0; padding: 28px; border-radius: 9px; color: #64748b; background: #f8fafc; text-align: center; }
@media (max-width: 600px) { .detail-page { padding: 24px 14px; }.info-grid { grid-template-columns: 1fr; } }
@media (max-width: 700px) { .attachment-item { grid-template-columns: auto 1fr; }.attachment-actions { grid-column: 1 / -1; justify-content: flex-end; } }
</style>
