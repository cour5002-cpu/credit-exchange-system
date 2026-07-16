<script setup>
const entries = [
  { title: '待审核成果', description: '查看等待审核的学生成果。', to: '/reviewer/review-tasks' },
  { title: '我的审核记录', description: '查看已经完成的审核记录。', to: '/reviewer/review-records' },
  { title: '信息通知', description: '查看审核老师端通知消息。', to: '/reviewer/notifications' },
]
</script>

<template>
  <main class="dashboard-page">
    <div class="dashboard-content">
      <header class="dashboard-header">
        <p class="eyebrow">REVIEWER PORTAL</p>
        <h1>审核老师端首页</h1>
        <p>欢迎进入课时 / 学分兑换系统审核工作台。</p>
      </header>

      <section class="entry-grid" aria-label="审核老师端功能入口">
        <RouterLink v-for="entry in entries" :key="entry.to" :to="entry.to" class="entry-card">
          <h2>{{ entry.title }}</h2>
          <p>{{ entry.description }}</p>
        </RouterLink>
      </section>
    </div>
  </main>
</template>
