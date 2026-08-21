<script setup>
import { onMounted, reactive, ref } from 'vue'
import PaginationControls from '../components/PaginationControls.vue'
import { adaptTaskType, getListItems } from '../adapters/commonAdapter.js'
import { adaptExtensionRuleEnvelope, adaptExtensionRuleList } from '../adapters/extensionRuleAdapter.js'
import { createExtensionRule, disableExtensionRule, enableExtensionRule, getExtensionRule, getExtensionRules, updateExtensionRule } from '../api/extensionRuleApi.js'
import { getAdminTaskTypes } from '../api/taskApi.js'

const PAGE_SIZE = 20
const status = ref('all')
const effective = ref('all')
const page = ref(1)
const total = ref(0)
const rules = ref([])
const taskTypeOptions = ref([])
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const formError = ref('')
const editingId = ref(null)
const showForm = ref(false)

const emptyForm = () => ({ ruleName: '', ordinaryMaxDays: '', specialThresholdDays: '', specialMaxDays: '', maxExtensionRequests: '', defaultMaterialDueDays: '', allowBeyondGraduation: false, taskTypeIds: [], effectiveAt: '', status: 'enabled', version: null })
const form = reactive(emptyForm())

function resetForm() { Object.assign(form, emptyForm()); formError.value = '' }
function apiError(error, fallback) {
  const responseStatus = Number(error?.status ?? error?.response?.status)
  if (responseStatus === 403) return '无权限维护延期规则。'
  if (responseStatus === 404) return '延期规则不存在。'
  return error?.message || fallback
}
function isConflict(error) { return Number(error?.code) === 40906 || Number(error?.status ?? error?.response?.status) === 409 }
function toLocalDateTime(value) { return value ? String(value).slice(0, 16) : '' }
function toApiDateTime(value) { return /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}:00+08:00` }
function taskTypeText(rule) { return rule.taskTypes.map((item) => item.name || item.code || item.id).join('、') || '--' }

async function loadRules() {
  loading.value = true
  rules.value = []
  total.value = 0
  errorMessage.value = ''
  try {
    const payload = await getExtensionRules({ status: status.value, effective: effective.value, page: page.value, page_size: PAGE_SIZE })
    const adapted = adaptExtensionRuleList(payload)
    rules.value = adapted.items
    total.value = Number(payload?.total ?? payload?.pagination?.total ?? rules.value.length) || 0
  } catch (error) {
    rules.value = []
    total.value = 0
    errorMessage.value = apiError(error, '延期规则加载失败。')
  } finally { loading.value = false }
}

async function loadTaskTypes() {
  try {
    taskTypeOptions.value = getListItems(await getAdminTaskTypes({ status: 'all', page_size: 100 })).map(adaptTaskType).filter(Boolean)
  } catch (error) { formError.value = apiError(error, '任务类型加载失败。') }
}

function applyFilters() { page.value = 1; loadRules() }
function changePage(next) { page.value = next; loadRules() }
async function openCreate() { editingId.value = null; resetForm(); showForm.value = true; if (!taskTypeOptions.value.length) await loadTaskTypes() }
async function openEdit(rule) {
  editingId.value = rule.id
  resetForm()
  showForm.value = true
  saving.value = true
  try {
    if (!taskTypeOptions.value.length) await loadTaskTypes()
    const current = adaptExtensionRuleEnvelope(await getExtensionRule(rule.id))
    Object.assign(form, {
      ruleName: current.ruleName,
      ordinaryMaxDays: current.ordinaryMaxDays,
      specialThresholdDays: current.specialThresholdDays,
      specialMaxDays: current.specialMaxDays,
      maxExtensionRequests: current.maxExtensionRequests,
      defaultMaterialDueDays: current.defaultMaterialDueDays,
      allowBeyondGraduation: Boolean(current.allowBeyondGraduation),
      taskTypeIds: current.taskTypes.map((item) => Number(item.id)),
      effectiveAt: toLocalDateTime(current.effectiveAt),
      status: current.status,
      version: current.version,
    })
  } catch (error) { formError.value = apiError(error, '延期规则详情加载失败。') }
  finally { saving.value = false }
}

function validate() {
  if (!form.ruleName.trim()) return '规则名称不能为空。'
  const fields = [['普通延期最大天数', form.ordinaryMaxDays], ['特殊延期阈值天数', form.specialThresholdDays], ['特殊延期最大天数', form.specialMaxDays], ['最大延期次数', form.maxExtensionRequests], ['默认成果期限天数', form.defaultMaterialDueDays]]
  const invalid = fields.find(([, value]) => !Number.isInteger(Number(value)) || Number(value) <= 0)
  if (invalid) return `${invalid[0]}必须是正整数。`
  if (Number(form.ordinaryMaxDays) > Number(form.specialMaxDays)) return '普通延期最大天数不能大于特殊延期最大天数。'
  if (Number(form.specialThresholdDays) > Number(form.specialMaxDays)) return '特殊延期阈值天数不能大于特殊延期最大天数。'
  if (!form.taskTypeIds.length) return '至少选择一个适用任务类型。'
  if (!form.effectiveAt) return '生效时间不能为空。'
  if (editingId.value && (!Number.isInteger(Number(form.version)) || Number(form.version) <= 0)) return '当前规则缺少有效版本号，请重新加载后再编辑。'
  return ''
}

function formPayload() {
  return {
    rule_name: form.ruleName.trim(),
    ordinary_max_days: Number(form.ordinaryMaxDays),
    special_threshold_days: Number(form.specialThresholdDays),
    special_max_days: Number(form.specialMaxDays),
    max_extension_requests: Number(form.maxExtensionRequests),
    default_material_due_days: Number(form.defaultMaterialDueDays),
    allow_beyond_graduation: Boolean(form.allowBeyondGraduation),
    task_type_ids: form.taskTypeIds.map(Number),
    effective_at: toApiDateTime(form.effectiveAt),
    status: form.status,
  }
}

async function saveRule() {
  formError.value = validate()
  if (formError.value) return
  saving.value = true
  try {
    const payload = formPayload()
    if (editingId.value) await updateExtensionRule(editingId.value, { ...payload, version: form.version })
    else await createExtensionRule(payload)
    showForm.value = false
    await loadRules()
  } catch (error) {
    formError.value = apiError(error, '延期规则保存失败。')
    if (isConflict(error)) { formError.value = error?.message || '数据已被其他管理员修改，请刷新后重试。'; await loadRules() }
  } finally { saving.value = false }
}

async function toggleRule(rule) {
  errorMessage.value = ''
  try {
    const action = rule.status === 'enabled' ? disableExtensionRule : enableExtensionRule
    await action(rule.id, { version: rule.version })
    await loadRules()
  } catch (error) {
    if (isConflict(error)) {
      const message = error?.message || '数据已被其他管理员修改，请刷新后重试。'
      await loadRules()
      window.alert(message)
    } else errorMessage.value = apiError(error, '延期规则状态修改失败。')
  }
}

onMounted(() => { loadRules(); loadTaskTypes() })
</script>

<template><main class="page"><div class="content">
  <header><div><p class="eyebrow">EXTENSION RULE MANAGEMENT</p><h1>延期规则管理</h1><p>配置延期范围、次数、默认成果期限和生效范围。</p></div><div class="header-actions"><RouterLink to="/admin/dashboard">返回首页</RouterLink><button class="primary" type="button" @click="openCreate">新增规则</button></div></header>
  <form class="filters" @submit.prevent="applyFilters"><label><span>状态</span><select v-model="status"><option value="all">全部</option><option value="enabled">已启用</option><option value="disabled">已停用</option></select></label><label><span>生效范围</span><select v-model="effective"><option value="all">全部</option><option value="current">当前生效</option><option value="future">未来生效</option></select></label><button type="submit" :disabled="loading">查询</button></form>
  <section v-if="showForm" class="form-panel"><div class="panel-head"><h2>{{ editingId ? '编辑延期规则' : '新增延期规则' }}</h2><button type="button" @click="showForm=false">关闭</button></div><div class="form-grid"><label><span>规则名称</span><input v-model="form.ruleName" /></label><label><span>普通延期最大天数</span><input v-model.number="form.ordinaryMaxDays" type="number" min="1" step="1" /></label><label><span>特殊延期阈值天数</span><input v-model.number="form.specialThresholdDays" type="number" min="1" step="1" /></label><label><span>特殊延期最大天数</span><input v-model.number="form.specialMaxDays" type="number" min="1" step="1" /></label><label><span>最大延期次数</span><input v-model.number="form.maxExtensionRequests" type="number" min="1" step="1" /></label><label><span>默认成果期限天数</span><input v-model.number="form.defaultMaterialDueDays" type="number" min="1" step="1" /></label><label><span>生效时间</span><input v-model="form.effectiveAt" type="datetime-local" /></label><label><span>状态</span><select v-model="form.status"><option value="enabled">已启用</option><option value="disabled">已停用</option></select></label><label class="checkbox"><input v-model="form.allowBeyondGraduation" type="checkbox" /><span>允许超过预计毕业日期</span></label><fieldset class="task-types"><legend>适用任务类型（至少选择一个）</legend><label v-for="option in taskTypeOptions" :key="option.id"><input v-model="form.taskTypeIds" type="checkbox" :value="Number(option.id)" />{{ option.label }}</label><p v-if="!taskTypeOptions.length">暂无可选任务类型。</p></fieldset></div><p v-if="formError" class="error" role="alert">{{ formError }}</p><div class="form-actions"><button type="button" @click="showForm=false">取消</button><button class="primary" type="button" :disabled="saving" @click="saveRule">{{ saving ? '保存中...' : '保存规则' }}</button></div></section>
  <section class="panel"><p v-if="loading" class="state">延期规则加载中...</p><p v-else-if="errorMessage" class="state error" role="alert">{{ errorMessage }}</p><p v-else-if="!rules.length" class="state">暂无延期规则。</p><div v-else class="table-wrap"><table><thead><tr><th>规则名称</th><th>普通最大天数</th><th>特殊阈值</th><th>特殊最大天数</th><th>最大次数</th><th>默认成果期限</th><th>允许超过毕业日期</th><th>适用任务类型</th><th>生效时间</th><th>状态</th><th>版本</th><th>操作</th></tr></thead><tbody><tr v-for="rule in rules" :key="rule.id"><td>{{ rule.ruleName }}</td><td>{{ rule.ordinaryMaxDays }}</td><td>{{ rule.specialThresholdDays }}</td><td>{{ rule.specialMaxDays }}</td><td>{{ rule.maxExtensionRequests }}</td><td>{{ rule.defaultMaterialDueDays }}</td><td>{{ rule.allowBeyondGraduation ? '是' : '否' }}</td><td class="task-type-text">{{ taskTypeText(rule) }}</td><td>{{ rule.effectiveAt }}</td><td>{{ rule.statusText }}</td><td>{{ rule.version }}</td><td><div class="row-actions"><button type="button" @click="openEdit(rule)">编辑</button><button type="button" @click="toggleRule(rule)">{{ rule.status === 'enabled' ? '停用' : '启用' }}</button></div></td></tr></tbody></table></div><PaginationControls v-if="!errorMessage" :page="page" :page-size="PAGE_SIZE" :total="total" :loading="loading" @change="changePage" /></section>
</div></main></template>

<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1500px);margin:auto}header,.header-actions,.filters,.panel-head,.form-actions,.row-actions{display:flex;align-items:center;justify-content:space-between;gap:12px}.eyebrow{color:#2563eb;font-size:12px;font-weight:800}.header-actions a,.header-actions button,.filters button,.panel-head button,.form-actions button,.row-actions button{padding:9px 14px;border:1px solid #cbd5e1;border-radius:8px;color:#2563eb;background:#fff;font-weight:700;text-decoration:none}.primary{border-color:#2563eb!important;color:#fff!important;background:#2563eb!important}.filters,.form-panel,.panel{margin-top:18px;padding:18px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.filters{justify-content:flex-start}.filters label{display:flex;align-items:center;gap:8px}.filters select,.form-grid input,.form-grid select{box-sizing:border-box;padding:10px;border:1px solid #cbd5e1;border-radius:8px}.form-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:18px}.form-grid>label{display:grid;gap:6px}.checkbox{display:flex!important;align-items:center;align-self:end}.checkbox input,.task-types input{width:auto}.task-types{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:14px;border:1px solid #e2e8f0;border-radius:8px;padding:14px}.task-types legend{font-weight:700}.task-types label{display:flex;gap:6px}.form-actions{justify-content:flex-end;margin-top:16px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top;white-space:nowrap}.task-type-text{min-width:180px;white-space:normal}.state{padding:30px;text-align:center;color:#64748b}.error{color:#b91c1c}@media(max-width:800px){header,.filters{align-items:flex-start;flex-direction:column}.form-grid{grid-template-columns:1fr}}</style>
