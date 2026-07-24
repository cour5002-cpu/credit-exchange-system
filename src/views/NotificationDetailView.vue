<script setup>
// 后端暂未实现通知接口，当前页面继续使用 Mock。
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { getNotificationById, markNotificationRead, NOTIFICATION_TYPES } from '../mock/notifications.js'
const props=defineProps({role:String,userId:String,pageCode:String,listPath:String})
const route=useRoute();const notification=computed(()=>{const item=getNotificationById(route.params.id);return item?.receiverRole===props.role&&item.receiverId===props.userId?item:null})
onMounted(()=>{if(notification.value)markNotificationRead(notification.value.notificationId)})
</script>
<template><main class="page"><div class="content"><template v-if="notification"><header><div><p class="eyebrow">{{ pageCode }} · NOTIFICATION DETAIL</p><h1>{{ notification.title }}</h1></div><StatusTag status="completed" text="已读" /></header><section class="card"><dl><div><dt>通知类型</dt><dd>{{ NOTIFICATION_TYPES[notification.type] || notification.type }}</dd></div><div><dt>创建时间</dt><dd>{{ notification.createTime }}</dd></div><div><dt>关联业务类型</dt><dd>{{ notification.relatedBizType || '--' }}</dd></div><div><dt>关联业务编号</dt><dd>{{ notification.relatedBizId || '--' }}</dd></div></dl></section><section class="card"><h2>通知内容</h2><p class="content-text">{{ notification.content }}</p></section><div class="actions"><RouterLink :to="listPath">返回通知列表</RouterLink></div></template><section v-else class="card"><h1>通知不存在</h1><RouterLink :to="listPath">返回通知列表</RouterLink></section></div></main></template>
<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,820px);margin:auto}header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}h1{margin:0}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800}.card{margin-bottom:18px;padding:24px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin-top:0}dl{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}dt{color:#64748b}dd{margin:5px 0 0;font-weight:700}.content-text{line-height:1.8;white-space:pre-wrap}.actions{text-align:right}.actions a,.card>a{display:inline-block;padding:10px 16px;border:1px solid #cbd5e1;border-radius:9px;color:#2563eb;background:#fff;font-weight:700;text-decoration:none}@media(max-width:600px){dl{grid-template-columns:1fr}}</style>
