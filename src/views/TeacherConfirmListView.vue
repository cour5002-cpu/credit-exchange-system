<script setup>
import { computed, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { getAdvisorPendingApplications } from '../mock/applications.js'

const selectedSource = ref('')
const keyword = ref('')

const filteredConfirmations = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase()
  return getAdvisorPendingApplications().filter((item) => {
    const matchesSource = !selectedSource.value || item.source === selectedSource.value
    const matchesKeyword =
      !normalizedKeyword ||
      item.studentName.toLowerCase().includes(normalizedKeyword) ||
      item.title.toLowerCase().includes(normalizedKeyword)
    return matchesSource && matchesKeyword
  })
})
</script>

<template>
  <main class="confirm-page">
    <div class="confirm-content">
      <header class="page-header">
        <div>
          <p class="eyebrow">PENDING CONFIRMATIONS</p>
          <h1>待确认事项</h1>
          <p>查看并处理学生提交的各类确认事项。</p>
        </div>
        <RouterLink class="secondary-link" to="/teacher/dashboard">返回教师首页</RouterLink>
      </header>

      <nav class="type-tabs" aria-label="待确认事项类型">
        <RouterLink class="active" to="/teacher/confirm">课时申请确认</RouterLink>
        <RouterLink to="/teacher/confirm/exchanges">学分兑换确认</RouterLink>
      </nav>

      <section class="filter-panel" aria-label="确认事项筛选">
        <label>
          <span>申请来源</span>
          <select v-model="selectedSource">
            <option value="">全部来源</option>
            <option value="self">学生自主申请</option>
            <option value="task">任务成果申请</option>
          </select>
        </label>
        <label>
          <span>搜索</span>
          <input v-model="keyword" type="search" placeholder="搜索学生姓名或事项标题" />
        </label>
      </section>

      <section class="list-panel" aria-labelledby="confirmation-list-title">
        <div class="panel-header">
          <h2 id="confirmation-list-title">确认事项列表</h2>
          <span>共 {{ filteredConfirmations.length }} 项</span>
        </div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>事项标题</th><th>学生姓名</th><th>确认类型</th><th>提交时间</th><th>当前状态</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredConfirmations" :key="item.id">
                <td><strong>{{ item.title }}</strong><small>{{ item.id }}</small></td>
                <td>{{ item.studentName }}</td>
                <td>课时申请确认</td>
                <td>{{ item.submitTime }}</td>
                <td><StatusTag :status="item.status" /></td>
                <td><RouterLink class="detail-link" :to="`/teacher/confirm/${item.id}`">查看详情</RouterLink></td>
              </tr>
              <tr v-if="!filteredConfirmations.length">
                <td class="empty-state" colspan="6">没有找到符合条件的确认事项。</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.confirm-page { min-height: 100vh; padding: 40px 24px; background: #f3f6fb; }
.confirm-content { width: min(100%, 1120px); margin: 0 auto; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; margin-bottom: 24px; }
.page-header h1 { margin: 0 0 8px; font-size: 30px; }.page-header p { color: #64748b; }
.secondary-link, .detail-link { color: #2563eb; font-weight: 700; text-decoration: none; }
.secondary-link { padding: 9px 14px; border: 1px solid #cbd5e1; border-radius: 9px; background: #fff; }
.type-tabs { display: flex; gap: 8px; margin-bottom: 18px; padding: 6px; border: 1px solid #e2e8f0; border-radius: 12px; background: #fff; }
.type-tabs a { padding: 10px 16px; border-radius: 8px; color: #475569; text-decoration: none; font-weight: 700; }
.type-tabs .active { color: #1d4ed8; background: #dbeafe; }
.filter-panel { display: grid; grid-template-columns: 260px 1fr; gap: 16px; margin-bottom: 20px; padding: 18px; border: 1px solid #e2e8f0; border-radius: 14px; background: #fff; }
.filter-panel label span { display: block; margin-bottom: 7px; color: #334155; font-weight: 700; }
.filter-panel select, .filter-panel input { width: 100%; padding: 10px 11px; border: 1px solid #cbd5e1; border-radius: 8px; background: #fff; font: inherit; }
.list-panel { overflow: hidden; border: 1px solid #e2e8f0; border-radius: 14px; background: #fff; }
.panel-header { display: flex; justify-content: space-between; padding: 18px 20px; border-bottom: 1px solid #e2e8f0; }.panel-header h2 { margin: 0; font-size: 19px; }.panel-header span { color: #64748b; }
.table-wrapper { overflow-x: auto; }table { width: 100%; border-collapse: collapse; }th, td { padding: 13px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; white-space: nowrap; }th { color: #475569; background: #f8fafc; font-size: 13px; }tbody tr:last-child td { border-bottom: 0; }td small { display: block; margin-top: 4px; color: #94a3b8; }.empty-state { padding: 32px; color: #64748b; text-align: center; }
@media (max-width: 680px) { .confirm-page { padding: 24px 14px; }.page-header { flex-direction: column; }.filter-panel { grid-template-columns: 1fr; } }
</style>
