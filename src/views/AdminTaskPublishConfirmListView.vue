<script setup>
import { computed, onMounted, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import { TASK_TYPE_OPTIONS, getTaskTypeText } from '../mock/tasks.js'
import { batchApproveTaskPublish, getTaskPublishRequests } from '../api/taskApi.js'
import { adaptTaskList } from '../adapters/taskAdapter.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'
const keyword=ref('');const selectedType=ref('');const selectedIds=ref([]);const batchComment=ref('');const batchResult=ref(null);const version=ref(0);const batchApproving=ref(false)
const remoteItems=ref([]);onMounted(loadItems)
async function loadItems(){try{remoteItems.value=adaptTaskList(await getTaskPublishRequests({page_size:100}))}catch(error){window.alert(getApiErrorMessage(error,'待确认任务加载失败'))}}
const items=computed(()=>{version.value;const search=keyword.value.trim().toLowerCase();return remoteItems.value.filter(item=>(!selectedType.value||item.taskTypeId===selectedType.value)&&(!search||item.title.toLowerCase().includes(search))).sort((a,b)=>String(b.submitTime).localeCompare(String(a.submitTime)))})
const allSelected=computed(()=>items.value.length>0&&items.value.every(item=>selectedIds.value.includes(item.taskId)))
const partiallySelected=computed(()=>!allSelected.value&&items.value.some(item=>selectedIds.value.includes(item.taskId)))
function toggleAll(event){const ids=items.value.map(item=>item.taskId);selectedIds.value=event.target.checked?[...new Set([...selectedIds.value,...ids])]:selectedIds.value.filter(id=>!ids.includes(id))}
function finish(result,action){batchResult.value={...result,action};selectedIds.value=[];version.value+=1}
async function approve(){
  if (!selectedIds.value.length) return window.alert('请先选择要确认发布的任务。')
  if (!window.confirm(`确定批量确认发布已选择的 ${selectedIds.value.length} 个任务吗？`)) return
  const taskIds=[...selectedIds.value]
  batchApproving.value=true
  try{
    const result=await batchApproveTaskPublish({task_ids:taskIds,comment:batchComment.value.trim()||null})
    const resultItems=result?.items??result?.results??[]
    const failedItems=result?.failed_items??resultItems.filter(item=>item.success===false).map(item=>({taskId:item.task_id??item.id,reason:item.reason??item.message??'处理失败'}))
    batchResult.value={
      action:'批量确认发布',
      total:result?.requested_count??taskIds.length,
      success:result?.success_count??resultItems.filter(item=>item.success===true).length,
      failed:result?.failed_count??failedItems.length,
      failedItems,
    }
    selectedIds.value=[]
    await loadItems()
  }catch(error){window.alert(getApiErrorMessage(error,'批量确认发布失败'))}
  finally{batchApproving.value=false}
}
function reject(){window.alert('请进入任务详情逐条驳回发布。')}
</script>
<template><main class="page"><div class="content"><header class="header"><div><p class="eyebrow">A101 · TASK PUBLISH CONFIRMATION</p><h1>任务发布确认</h1><p>确认指导老师提交并等待发布到学生端的任务。</p></div><RouterLink class="back" to="/admin/tasks">返回任务管理</RouterLink></header>
<section class="filters"><label><span>任务名称</span><input v-model="keyword" type="search" placeholder="搜索任务名称" /></label><label><span>任务类型</span><select v-model="selectedType"><option value="">全部类型</option><option v-for="option in TASK_TYPE_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option></select></label><label><span>批量处理意见</span><input v-model="batchComment" placeholder="批量驳回时必填" /></label></section>
<section v-if="batchResult" class="result"><strong>{{ batchResult.action }}结果</strong><p>本次处理 {{ batchResult.total }} 条，成功 {{ batchResult.success }} 条，失败 {{ batchResult.failed }} 条。</p><ul v-if="batchResult.failedItems.length"><li v-for="failed in batchResult.failedItems" :key="failed.taskId">{{ failed.taskId }}：{{ failed.reason }}</li></ul></section>
<section class="panel"><div class="panel-head"><div><h2>待确认发布任务</h2><span>共 {{ items.length }} 条，已选择 {{ selectedIds.length }} 条</span></div><div class="batch-actions"><button class="approve" :disabled="batchApproving||!selectedIds.length" @click="approve">{{ batchApproving?'批量确认中...':'批量确认发布' }}</button><button class="reject" @click="reject">批量驳回发布</button></div></div><div class="table-wrap"><table><thead><tr><th><input type="checkbox" aria-label="全选任务" :checked="allSelected" :indeterminate.prop="partiallySelected" :disabled="!items.length||batchApproving" @change="toggleAll" /></th><th>任务名称</th><th>发布人 / 指导老师</th><th>任务类型</th><th>报名截止时间</th><th>提交时间</th><th>附件数量</th><th>当前确认状态</th><th>任务来源</th><th>操作</th></tr></thead><tbody><tr v-for="item in items" :key="item.taskId"><td><input v-model="selectedIds" type="checkbox" :value="item.taskId" :disabled="batchApproving" /></td><td><strong>{{ item.title }}</strong><small>{{ item.taskId }}</small></td><td>{{ item.advisorName }}<small>{{ item.advisorId }}</small></td><td>{{ getTaskTypeText(item.taskType) }}</td><td>{{ item.registrationDeadline }}</td><td>{{ item.submitTime||'--' }}</td><td>{{ item.attachments?.length||0 }}</td><td><StatusTag :status="item.status" /></td><td>指导老师发布</td><td><RouterLink class="detail" :to="`/admin/tasks/publish-confirm/${item.taskId}`">查看详情</RouterLink></td></tr><tr v-if="!items.length"><td class="empty" colspan="10">暂无待确认发布的任务。</td></tr></tbody></table></div></section></div></main></template>
<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1420px);margin:auto}.header,.panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}.header{margin-bottom:20px}.header h1{margin:0 0 8px}.header p{color:#64748b}.eyebrow{margin:0 0 6px;color:#2563eb!important;font-size:12px;font-weight:800;letter-spacing:.12em}.back,.detail{color:#2563eb;font-weight:700;text-decoration:none}.back{padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.filters{display:grid;grid-template-columns:1fr 260px 1fr;gap:16px;margin-bottom:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;font-weight:700}.filters input,.filters select{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.result{margin-bottom:18px;padding:16px;border:1px solid #86efac;border-radius:12px;color:#166534;background:#f0fdf4}.result p{margin:6px 0}.panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-head{align-items:center;padding:18px 20px}.panel-head h2{margin:0 0 5px}.panel-head span{color:#64748b}.batch-actions{display:flex;gap:10px}.batch-actions button{padding:9px 14px;border:0;border-radius:9px;color:#fff;font:inherit;font-weight:700;cursor:pointer}.approve{background:#2563eb}.reject{background:#dc2626}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-top:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{background:#f8fafc;font-size:13px}td small{display:block;margin-top:4px;color:#94a3b8}input[type=checkbox]{width:17px;height:17px;accent-color:#2563eb}.empty{padding:34px;text-align:center;color:#64748b}@media(max-width:800px){.page{padding:24px 14px}.header,.panel-head{flex-direction:column}.filters{grid-template-columns:1fr}.batch-actions{flex-wrap:wrap}}</style>
