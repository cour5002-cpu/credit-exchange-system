<script setup>
import { computed, onMounted, ref } from 'vue'
import { getUnreadCount } from '../api/notificationApi.js'

defineProps({
  to: { type: String, required: true },
  description: { type: String, default: '查看通知消息。' },
})

const unreadCount = ref(0)
const loading = ref(false)
const failed = ref(false)
const countText = computed(() => loading.value ? '…' : failed.value ? '--' : unreadCount.value)

async function loadUnreadCount() {
  if (loading.value) return
  loading.value = true
  failed.value = false
  try {
    const payload = await getUnreadCount()
    unreadCount.value = Number(typeof payload === 'number' ? payload : payload?.unread_count ?? payload?.count ?? 0)
  } catch (error) {
    failed.value = true
    console.warn('[notification-badge] 未读消息数量加载失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(loadUnreadCount)
</script>

<template>
  <RouterLink :to="to" class="notification-entry">
    <div class="notification-entry__heading">
      <h2>信息通知</h2>
      <strong :title="failed ? '未读数量加载失败' : '未读消息数量'">{{ countText }}</strong>
    </div>
    <p>{{ description }}</p>
  </RouterLink>
</template>

<style scoped>
.notification-entry{padding:24px;border:1px solid #e2e8f0;border-radius:16px;color:#0f172a;background:#fff;text-decoration:none;box-shadow:0 8px 25px rgba(15,23,42,.05)}.notification-entry__heading{display:flex;align-items:center;justify-content:space-between;gap:12px}.notification-entry h2{margin:0;font-size:20px}.notification-entry strong{min-width:36px;padding:6px 10px;border-radius:999px;color:#1d4ed8;background:#dbeafe;text-align:center}.notification-entry p{margin:14px 0 0;color:#64748b;line-height:1.6}
</style>
