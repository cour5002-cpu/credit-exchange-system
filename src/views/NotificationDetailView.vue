<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { getNotificationDetail, markNotificationRead } from '../api/notificationApi.js'
import { adaptNotification } from '../adapters/notificationAdapter.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'
import { getNotificationBizPath } from '../utils/notificationRouterMap.js'

const props=defineProps({role:String,userId:String,pageCode:String,listPath:String})
const route = useRoute()
const notification = ref(null)
const loading = ref(true)
const errorMessage = ref('')
const businessPath = computed(() => getNotificationBizPath(notification.value, props.role))
const businessUnavailable = computed(() => notification.value?.bizAvailable === false)

async function loadNotification() {
  loading.value = true
  errorMessage.value = ''
  try {
    const payload = await getNotificationDetail(route.params.id)
    notification.value = adaptNotification(payload?.notification ?? payload)
    if (!notification.value) {
      errorMessage.value = '消息不存在'
      return
    }
    if (notification.value.isRead === false) {
      try {
        await markNotificationRead(notification.value.id)
        notification.value = { ...notification.value, isRead: true }
      } catch (error) {
        window.alert(getApiErrorMessage(error, '消息标记已读失败，请稍后重试'))
      }
    }
  } catch (error) {
    notification.value = null
    errorMessage.value = error?.status === 404 || error?.code === 40401
      ? '消息不存在'
      : getApiErrorMessage(error, '消息详情加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(loadNotification)
</script>
<template><main class="page"><div class="content"><section v-if="loading" class="card"><h1>消息加载中...</h1></section><template v-else-if="notification"><header><div><p class="eyebrow">{{ pageCode }} · NOTIFICATION DETAIL</p><h1>{{ notification.title }}</h1></div><StatusTag :status="notification.isRead?'completed':'pending'" :text="notification.isRead?'已读':'未读'" /></header><section class="card"><dl><div><dt>通知类型</dt><dd>{{ notification.category || notification.messageType || '--' }}</dd></div><div><dt>创建时间</dt><dd>{{ notification.createdAt }}</dd></div><div><dt>关联业务类型</dt><dd>{{ notification.bizType || '--' }}</dd></div><div><dt>关联业务编号</dt><dd>{{ notification.bizId || '--' }}</dd></div></dl></section><section class="card"><h2>通知内容</h2><p class="content-text">{{ notification.content }}</p></section><div class="actions"><span v-if="businessUnavailable">该业务已不可访问</span><RouterLink v-else-if="businessPath" :to="businessPath">查看关联业务</RouterLink> <RouterLink :to="listPath">返回通知列表</RouterLink></div></template><section v-else class="card"><h1>{{ errorMessage || '消息不存在' }}</h1><RouterLink :to="listPath">返回通知列表</RouterLink></section></div></main></template>
<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,820px);margin:auto}header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}h1{margin:0}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800}.card{margin-bottom:18px;padding:24px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin-top:0}dl{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}dt{color:#64748b}dd{margin:5px 0 0;font-weight:700}.content-text{line-height:1.8;white-space:pre-wrap}.actions{text-align:right}.actions a,.card>a{display:inline-block;padding:10px 16px;border:1px solid #cbd5e1;border-radius:9px;color:#2563eb;background:#fff;font-weight:700;text-decoration:none}@media(max-width:600px){dl{grid-template-columns:1fr}}</style>
