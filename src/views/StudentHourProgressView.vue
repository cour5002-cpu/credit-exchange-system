<script setup>
import { computed, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { APPLICATION_STATUS, canSupplementResult, getApplications } from '../mock/applications.js'
import { getStatusText } from '../utils/status.js'

const currentUser = { id: 'stu001', name: '张三', studentId: '2024001' }
const selectedStatus = ref('')
const keyword = ref('')

const statusOptions = [
  APPLICATION_STATUS.PENDING_ADVISOR,
  APPLICATION_STATUS.PENDING_RESULT,
  APPLICATION_STATUS.NEED_SUPPLEMENT_RESULT,
  APPLICATION_STATUS.PENDING_MATERIAL,
  APPLICATION_STATUS.MATERIAL_SUBMITTED,
  APPLICATION_STATUS.SUPPLEMENT_REJECTED,
  APPLICATION_STATUS.PENDING_ADMIN_ACCEPT,
  APPLICATION_STATUS.PENDING_REVIEWER,
  APPLICATION_STATUS.PENDING_ADMIN_FINAL,
  APPLICATION_STATUS.ADVISOR_REJECTED,
  APPLICATION_STATUS.REVIEWER_REJECTED,
  APPLICATION_STATUS.FINAL_APPROVED,
  APPLICATION_STATUS.FINAL_REJECTED,
]

const applications = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return getApplications()
    .filter((application) => application.currentUserId === currentUser.id)
    .filter((application) => !selectedStatus.value || application.status === selectedStatus.value)
    .filter((application) => !search || application.title.toLowerCase().includes(search))
    .sort((a, b) => b.submitTime.localeCompare(a.submitTime))
})
</script>

<template>
  <main class="progress-page">
    <div class="page-content">
      <header class="page-header">
        <div>
          <p class="eyebrow">APPLICATION PROGRESS</p>
          <h1>课时申请进度</h1>
          <p>查看你提交的课时申请、当前处理状态和最终结果。</p>
        </div>
        <RouterLink class="back-link" to="/student/dashboard">返回学生首页</RouterLink>
      </header>

      <section class="filters" aria-label="申请进度筛选">
        <label>
          <span>当前状态</span>
          <select v-model="selectedStatus">
            <option value="">全部状态</option>
            <option v-for="status in statusOptions" :key="status" :value="status">
              {{ getStatusText(status) }}
            </option>
          </select>
        </label>
        <label>
          <span>搜索申请</span>
          <input v-model="keyword" type="search" placeholder="请输入申请标题" />
        </label>
      </section>

      <section class="list-panel" aria-labelledby="progress-list-title">
        <div class="panel-header">
          <h2 id="progress-list-title">我的申请</h2>
          <span>共 {{ applications.length }} 条</span>
        </div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>申请标题</th>
                <th>申请来源</th>
                <th>申请类型</th>
                <th>申请课时数</th>
                <th>当前状态</th>
                <th>提交时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="application in applications" :key="application.id">
                <td><strong>{{ application.title }}</strong><small>{{ application.id }}</small></td>
                <td>{{ application.sourceText }}</td>
                <td>{{ application.applyTypeText }}</td>
                <td>{{ application.requestedHours }} 小时</td>
                <td><StatusTag :status="application.status" /></td>
                <td>{{ application.submitTime }}</td>
                <td>
                  <RouterLink class="detail-link" :to="`/student/hour-progress/${application.id}`">
                    查看详情
                  </RouterLink>
                  <RouterLink v-if="canSupplementResult(application)" class="detail-link" :to="`/student/hour-progress/${application.id}/supplement-result`">补交成果</RouterLink>
                </td>
              </tr>
              <tr v-if="!applications.length">
                <td class="empty" colspan="7">暂无符合条件的课时申请。</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.progress-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.page-content{width:min(100%,1180px);margin:0 auto}.page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:24px}.page-header h1{margin:0 0 8px;font-size:30px}.page-header p{color:#64748b}.back-link,.detail-link{color:#2563eb;font-weight:700;text-decoration:none}.back-link{padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.filters{display:grid;grid-template-columns:280px 1fr;gap:16px;margin-bottom:20px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;color:#334155;font-weight:700}.filters select,.filters input{width:100%;padding:10px 11px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.list-panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-header{display:flex;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e2e8f0}.panel-header h2{margin:0;font-size:19px}.panel-header span{color:#64748b}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:13px 14px;border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{color:#475569;background:#f8fafc;font-size:13px}tbody tr:last-child td{border-bottom:0}td small{display:block;margin-top:4px;color:#94a3b8}.empty{padding:36px;color:#64748b;text-align:center}@media(max-width:680px){.progress-page{padding:24px 14px}.page-header{flex-direction:column}.filters{grid-template-columns:1fr}}
</style>
