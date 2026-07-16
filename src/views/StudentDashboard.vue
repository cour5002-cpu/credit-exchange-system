<script setup>
const entries = [
  { title: '我的任务', description: '查看和管理分配给你的任务。', to: '/student/tasks' },
  { title: '任务广场', description: '浏览当前可以参与的任务。', to: '/student/task-square' },
  { title: '课时申请', description: '提交新的课时认定申请。', to: '/student/hour-apply' },
  { title: '课时申请进度', description: '查看课时申请的处理状态。', to: '/student/hour-progress' },
  { title: '学分兑换', description: '办理课时与学分兑换。', to: '/student/credit-exchange' },
  { title: '问题反馈', description: '提交使用过程中遇到的问题。', to: '/student/feedback' },
  { title: '信息通知', description: '查看学生端通知消息。', to: '/student/notifications' },
]
</script>

<template>
  <main class="dashboard-page">
    <div class="dashboard-content">
      <header class="dashboard-header">
        <p class="eyebrow">STUDENT PORTAL</p>
        <h1>学生端首页</h1>
        <p>欢迎进入课时 / 学分兑换系统学生工作台。</p>
      </header>

      <section class="entry-grid" aria-label="学生端功能入口">
        <RouterLink v-for="entry in entries" :key="entry.to" :to="entry.to" class="entry-card">
          <h2>{{ entry.title }}</h2>
          <p>{{ entry.description }}</p>
        </RouterLink>
      </section>
    </div>
  </main>
</template>
