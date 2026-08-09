<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import PaginationControls from '../components/PaginationControls.vue'
import { getNotifications, getUnreadCount, markAllNotificationsRead } from '../api/notificationApi.js'
import { adaptNotification } from '../adapters/notificationAdapter.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const props = defineProps({ role: String, userId: String, pageCode: String, portalName: String, backPath: String, detailBase: String })
const type = ref('')
const readState = ref('')
const keyword = ref('')
const notifications = ref([])
const unread = ref(0)
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)
const errorMessage = ref('')

const typeOptions = computed(() => [...new Set(notifications.value.map((item) => item.category || item.messageType).filter(Boolean))])
const items = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return notifications.value.filter((item) => {
    const itemType = item.category || item.messageType
    return (!type.value || itemType === type.value)
      && (!search || item.title?.toLowerCase().includes(search) || item.content?.toLowerCase().includes(search))
  })
})

async function loadNotifications() {
  loading.value = true
  errorMessage.value = ''
  try {
    const payload = await getNotifications({
      page: page.value,
      page_size: pageSize,
      status: readState.value || undefined,
    })
    const sourceItems = Array.isArray(payload) ? payload : payload?.items ?? payload?.notifications ?? []
    notifications.value = sourceItems.map(adaptNotification).filter(Boolean)
    total.value = Number(Array.isArray(payload) ? payload.length : payload?.total ?? payload?.pagination?.total ?? sourceItems.length)
  } catch (error) {
    notifications.value = []
    total.value = 0
    errorMessage.value = getApiErrorMessage(error, '消息列表加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function loadUnreadCount() {
  try {
    const payload = await getUnreadCount()
    unread.value = Number(typeof payload === 'number' ? payload : payload?.unread_count ?? payload?.count ?? 0)
  } catch (error) {
    errorMessage.value ||= getApiErrorMessage(error, '未读消息数量加载失败，请稍后重试')
  }
}

async function markAll() {
  loading.value = true
  errorMessage.value = ''
  try {
    await markAllNotificationsRead()
    await Promise.all([loadNotifications(), loadUnreadCount()])
    window.alert('已全部标记为已读。')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '全部标记已读失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function changePage(nextPage) {
  page.value = nextPage
  loadNotifications()
}

watch(readState, () => {
  page.value = 1
  loadNotifications()
})

onMounted(() => Promise.all([loadNotifications(), loadUnreadCount()]))
</script>
<template><main class="page"><div class="content"><header><div><p class="eyebrow">{{ pageCode }} · NOTIFICATIONS</p><h1>信息通知</h1><p>{{ portalName }}通知中心，当前未读 {{ unread }} 条。</p></div><RouterLink class="back" :to="backPath">返回首页</RouterLink></header><section class="filters"><label><span>通知类型</span><select v-model="type"><option value="">全部类型</option><option v-for="value in typeOptions" :key="value" :value="value">{{ value }}</option></select></label><label><span>阅读状态</span><select v-model="readState"><option value="">全部</option><option value="unread">未读</option><option value="read">已读</option></select></label><label><span>搜索</span><input v-model="keyword" placeholder="搜索通知标题或内容" /></label><button :disabled="loading" @click="markAll">全部标记已读</button></section><section class="panel"><div class="head"><h2>通知列表</h2><span>共 {{ total }} 条</span></div><div class="list"><RouterLink v-for="item in items" :key="item.id" :to="`${detailBase}/${item.id}`" class="notice" :class="{unread:!item.isRead}"><i></i><div class="main"><div class="title"><strong>{{ item.title }}</strong><StatusTag :status="item.isRead?'completed':'pending'" :text="item.isRead?'已读':'未读'" /></div><p>{{ item.content }}</p><small>{{ item.category || item.messageType || '--' }} · {{ item.createdAt }}</small></div><span class="view">查看详情</span></RouterLink><p v-if="loading" class="empty">消息加载中...</p><p v-else-if="errorMessage" class="empty">{{ errorMessage }}</p><p v-else-if="!items.length" class="empty">暂无通知</p></div><PaginationControls :page="page" :page-size="pageSize" :total="total" :loading="loading" @change="changePage" /></section></div></main></template>
<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1040px);margin:auto}header,.head{display:flex;justify-content:space-between;gap:20px}header{margin-bottom:20px}h1{margin:0}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800}.back{color:#2563eb;font-weight:700;text-decoration:none}.filters{display:grid;grid-template-columns:190px 170px 1fr auto;align-items:end;gap:14px;margin-bottom:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;font-weight:700}.filters select,.filters input,.filters button{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.filters button{width:auto;color:#fff;background:#2563eb;font-weight:700}.panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.head{padding:18px 20px}.head h2{margin:0}.head span{color:#64748b}.notice{display:flex;align-items:center;gap:14px;padding:17px 20px;border-top:1px solid #e2e8f0;color:#0f172a;text-decoration:none}.notice.unread{background:#eff6ff}.notice>i{width:9px;height:9px;border-radius:50%;background:transparent}.notice.unread>i{background:#2563eb}.main{min-width:0;flex:1}.title{display:flex;align-items:center;gap:10px}.main p{overflow:hidden;margin:7px 0;color:#475569;text-overflow:ellipsis;white-space:nowrap}.main small{color:#64748b}.view{color:#2563eb;font-weight:700}.empty{padding:36px;text-align:center;color:#64748b}@media(max-width:760px){.filters{grid-template-columns:1fr}.filters button{width:100%}.notice{align-items:flex-start}.view{display:none}}</style>
