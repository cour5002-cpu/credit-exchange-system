<script setup>
import { ref } from 'vue'
import ImportInfoModal from './components/ImportInfoModal.vue'

const showImportModal = ref(false)

const entries = [
  { title: '任务管理', description: '维护系统中的任务信息。', to: '/admin/tasks' },
  { title: '审核分配', description: '为待审核事项分配审核老师。', to: '/admin/review-assign' },
  { title: '最终确认', description: '处理等待最终确认的业务。', to: '/admin/final-confirm' },
  { title: '申诉与投诉', description: '处理用户提交的申诉与投诉。', to: '/admin/appeals-complaints' },
  { title: '申诉复审分配', description: '为已受理申诉分配复审老师。', to: '/admin/appeals-complaints/assign' },
  { title: '特殊延期', description: '管理特殊情况的延期申请。', to: '/admin/extensions' },
  { title: '数据统计', description: '查看系统业务统计数据。', to: '/admin/statistics' },
  { title: '信息通知', description: '查看管理员端通知消息。', to: '/admin/notifications' },
]
</script>

<template>
  <main class="dashboard-page">
    <div class="dashboard-content">
      <header class="dashboard-header">
        <div>
          <p class="eyebrow">ADMIN PORTAL</p>
          <h1>管理端首页</h1>
          <p>欢迎进入课时 / 学分兑换系统管理工作台。</p>
        </div>
        <button class="primary-button" type="button" @click="showImportModal = true">
          导入信息
        </button>
      </header>

      <section class="entry-grid" aria-label="管理端功能入口">
        <RouterLink v-for="entry in entries" :key="entry.to" :to="entry.to" class="entry-card">
          <h2>{{ entry.title }}</h2>
          <p>{{ entry.description }}</p>
        </RouterLink>
      </section>
    </div>

    <ImportInfoModal v-if="showImportModal" @close="showImportModal = false" />
  </main>
</template>
