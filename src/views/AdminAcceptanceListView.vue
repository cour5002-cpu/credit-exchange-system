<script setup>
import { computed, ref } from 'vue'
import StatusTag from '../components/StatusTag.vue'
import {
  adminAccept,
  getAdminAcceptApplications,
} from '../mock/applications.js'

const selectedType = ref('')
const keyword = ref('')
const selectedIds = ref([])
const refreshKey = ref(0)

const filteredItems = computed(() => {
  refreshKey.value
  const search = keyword.value.trim().toLowerCase()
  return getAdminAcceptApplications().filter((item) =>
    (!selectedType.value || item.applyType === selectedType.value) &&
    (!search || item.studentName.toLowerCase().includes(search) || item.title.toLowerCase().includes(search)),
  )
})

const selectableItems = computed(() => filteredItems.value)
const allSelected = computed(() =>
  selectableItems.value.length > 0 && selectableItems.value.every((item) => selectedIds.value.includes(item.id)),
)
const partiallySelected = computed(() =>
  !allSelected.value && selectableItems.value.some((item) => selectedIds.value.includes(item.id)),
)

function toggleSelectAll(event) {
  const selectableIds = selectableItems.value.map((item) => item.id)
  selectedIds.value = event.target.checked
    ? [...new Set([...selectedIds.value, ...selectableIds])]
    : selectedIds.value.filter((id) => !selectableIds.includes(id))
}

function batchAccept() {
  if (!selectedIds.value.length) {
    window.alert('请先选择要受理的申请')
    return
  }

  const selectedItems = getAdminAcceptApplications().filter((item) => selectedIds.value.includes(item.id))
  if (!selectedItems.length) return

  if (!window.confirm(`确定要批量受理并分配已选择的 ${selectedItems.length} 条申请吗？`)) return

  const assignments = selectedItems.map((item) => {
    const acceptedApplication = adminAccept(item.id, '管理员批量受理并分配')
    return `${item.title} → ${acceptedApplication.reviewer.name}老师`
  })
  selectedIds.value = []
  refreshKey.value += 1
  window.alert(`批量受理并分配成功：\n${assignments.join('\n')}`)
}
</script>

<template>
  <main class="acceptance-page">
    <div class="page-content">
      <header class="page-header">
        <div><p class="eyebrow">ADMIN ACCEPTANCE</p><h1>待受理申请</h1><p>受理已经由指导老师确认通过的学生申请。</p></div>
        <RouterLink class="back-link" to="/admin/dashboard">返回管理首页</RouterLink>
      </header>

      <section class="filters" aria-label="待受理申请筛选">
        <label><span>申请类型</span><select v-model="selectedType"><option value="">全部类型</option><option value="with_result">有成果申请</option><option value="without_result">无成果申请</option></select></label>
        <label><span>搜索</span><input v-model="keyword" type="search" placeholder="搜索学生姓名或申请标题" /></label>
      </section>

      <section class="list-panel">
        <div class="panel-header">
          <div><h2>申请列表</h2><span>共 {{ filteredItems.length }} 项，已选择 {{ selectedIds.length }} 项</span></div>
          <button class="batch-button" type="button" @click="batchAccept">批量受理并分配</button>
        </div>
        <div class="table-wrapper"><table>
          <thead><tr>
            <th class="checkbox-cell"><input type="checkbox" aria-label="全选待受理申请" :checked="allSelected" :indeterminate.prop="partiallySelected" :disabled="!selectableItems.length" @change="toggleSelectAll" /></th>
            <th>申请标题</th><th>学生姓名</th><th>申请来源</th><th>申请类型</th><th>申请课时数</th><th>指导老师确认状态</th><th>拟分配审核老师</th><th>提交时间</th><th>当前状态</th><th>操作</th>
          </tr></thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td class="checkbox-cell"><input v-model="selectedIds" type="checkbox" :value="item.id" :aria-label="`选择申请：${item.title}`" /></td>
              <td><strong>{{ item.title }}</strong><small>{{ item.id }}</small></td><td>{{ item.studentName }}</td><td>{{ item.sourceText }}</td><td>{{ item.applyTypeText }}</td><td>{{ item.requestedHours }} 小时</td><td><StatusTag :status="item.advisorStatus" text="已确认" /></td><td>{{ item.reviewer?.name || '待分配' }}</td><td>{{ item.submitTime }}</td><td><StatusTag :status="item.status" text="待受理" /></td><td><RouterLink class="detail-link" :to="`/admin/review-assign/${item.id}`">查看详情</RouterLink></td>
            </tr>
            <tr v-if="!filteredItems.length"><td class="empty" colspan="11">没有找到符合条件的待受理申请。</td></tr>
          </tbody>
        </table></div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.acceptance-page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.page-content{width:min(100%,1180px);margin:0 auto}.page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:24px}.page-header h1{margin:0 0 8px;font-size:30px}.page-header p{color:#64748b}.back-link,.detail-link{color:#2563eb;font-weight:700;text-decoration:none}.back-link{padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;background:#fff}.filters{display:grid;grid-template-columns:260px 1fr;gap:16px;margin-bottom:20px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters span{display:block;margin-bottom:7px;color:#334155;font-weight:700}.filters select,.filters input{width:100%;padding:10px 11px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.list-panel{overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.panel-header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 20px;border-bottom:1px solid #e2e8f0}.panel-header h2{margin:0 0 4px;font-size:19px}.panel-header span{color:#64748b;font-size:13px}.batch-button{padding:9px 14px;border:1px solid #2563eb;border-radius:9px;color:#fff;background:#2563eb;font:inherit;font-weight:700;cursor:pointer;white-space:nowrap}.table-wrapper{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:13px 14px;border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap}th{color:#475569;background:#f8fafc;font-size:13px}.checkbox-cell{width:48px;text-align:center}.checkbox-cell input{width:17px;height:17px;accent-color:#2563eb;cursor:pointer}.checkbox-cell input:disabled{cursor:not-allowed}td small{display:block;margin-top:4px;color:#94a3b8}.empty{padding:32px;color:#64748b;text-align:center}@media(max-width:680px){.acceptance-page{padding:24px 14px}.page-header{flex-direction:column}.filters{grid-template-columns:1fr}.panel-header{align-items:stretch;flex-direction:column}}
</style>
