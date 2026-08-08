<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { uploadAttachment } from '../api/fileApi.js'
import { createRuleFile, getRuleFiles } from '../api/ruleFileApi.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'
import RuleFileViewer from '../components/RuleFileViewer.vue'

const items = ref([])
const keyword = ref('')
const loading = ref(false)
const uploading = ref(false)
const fileInput = ref(null)
const selectedFile = ref(null)
const form = reactive({ title: '', ruleType: 'other', usageType: 'reference_only' })

const visibleItems = computed(() => {
  const value = keyword.value.trim().toLowerCase()
  if (!value) return items.value
  return items.value.filter((item) => [item.title, item.attachment?.file_name]
    .some((text) => String(text || '').toLowerCase().includes(value)))
})

function formatTime(value) {
  if (!value) return '--'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

async function loadRuleFiles() {
  loading.value = true
  try {
    const payload = await getRuleFiles(keyword.value.trim() ? { keyword: keyword.value.trim() } : undefined)
    items.value = Array.isArray(payload) ? payload : payload?.items ?? []
  } catch (error) {
    window.alert(getApiErrorMessage(error, '规则文件列表加载失败'))
  } finally {
    loading.value = false
  }
}

function selectFile(event) {
  selectedFile.value = event.target.files?.[0] || null
  if (selectedFile.value && !form.title.trim()) form.title = selectedFile.value.name.replace(/\.[^.]+$/, '')
}

async function uploadRuleFile() {
  if (!selectedFile.value) return window.alert('请选择规则文件')
  if (!form.title.trim()) return window.alert('请输入规则文件标题')
  uploading.value = true
  try {
    const uploaded = await uploadAttachment(selectedFile.value, 'rule_file')
    await createRuleFile({
      title: form.title.trim(),
      rule_type: form.ruleType,
      usage_type: form.usageType,
      attachment_id: Number(uploaded.id),
    })
    form.title = ''
    form.ruleType = 'other'
    form.usageType = 'reference_only'
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    await loadRuleFiles()
    window.alert('规则文件上传成功')
  } catch (error) {
    window.alert(getApiErrorMessage(error, '规则文件上传失败'))
  } finally {
    uploading.value = false
  }
}

onMounted(loadRuleFiles)
</script>

<template>
  <main class="page">
    <div class="content">
      <header class="page-header">
        <div><p class="eyebrow">RULE FILE MANAGEMENT</p><h1>规则文件管理</h1><p>上传并维护供系统用户查阅的规则文件。</p></div>
        <RouterLink class="back" to="/admin/dashboard">返回管理首页</RouterLink>
      </header>

      <section class="card upload-card">
        <h2>上传规则文件</h2>
        <div class="form-grid">
          <label><span>文件标题</span><input v-model="form.title" placeholder="请输入规则文件标题" /></label>
          <label><span>规则类型</span><select v-model="form.ruleType"><option value="hour_rule">课时规则</option><option value="credit_rule">学分规则</option><option value="other">其他规则</option></select></label>
          <label><span>使用方式</span><select v-model="form.usageType"><option value="reference_only">仅供查阅</option><option value="calculation_basis">计算依据</option></select></label>
          <label><span>选择文件</span><input ref="fileInput" type="file" @change="selectFile" /></label>
        </div>
        <div class="upload-actions"><span>{{ selectedFile?.name || '尚未选择文件' }}</span><button :disabled="uploading" @click="uploadRuleFile">{{ uploading ? '正在上传...' : '上传文件' }}</button></div>
      </section>

      <section class="card">
        <div class="toolbar"><div><h2>规则文件列表</h2><span>共 {{ visibleItems.length }} 个文件</span></div><form @submit.prevent="loadRuleFiles"><input v-model="keyword" placeholder="搜索文件标题" /><button :disabled="loading">查询</button></form></div>
        <div class="table-wrap"><table><thead><tr><th>文件名称</th><th>文件类型</th><th>上传时间</th><th>操作</th></tr></thead><tbody>
          <tr v-for="item in visibleItems" :key="item.id"><td><strong>{{ item.title }}</strong><small>{{ item.attachment?.file_name || '--' }}</small></td><td>{{ item.attachment?.mime_type || item.rule_type || '--' }}</td><td>{{ formatTime(item.created_at || item.attachment?.created_at) }}</td><td><RuleFileViewer :item="item" :show-name="false" /></td></tr>
          <tr v-if="loading"><td colspan="4" class="empty">正在加载...</td></tr><tr v-else-if="!visibleItems.length"><td colspan="4" class="empty">暂无规则文件</td></tr>
        </tbody></table></div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,1040px);margin:auto}.page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:22px}.page-header h1{margin:0}.page-header p{color:#64748b}.eyebrow{margin:0 0 6px!important;color:#2563eb!important;font-size:12px;font-weight:800;letter-spacing:.12em}.back{padding:9px 14px;border:1px solid #cbd5e1;border-radius:9px;color:#2563eb;background:#fff;text-decoration:none}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:18px}.form-grid label{display:grid;gap:7px;color:#334155;font-weight:700}.form-grid input,.form-grid select,.toolbar input{box-sizing:border-box;width:100%;padding:10px 11px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font:inherit}.upload-actions,.toolbar,.toolbar>div,.toolbar form{display:flex;align-items:center}.upload-actions{justify-content:space-between;gap:16px;margin-top:18px;color:#64748b}.upload-actions button,.toolbar button,.download{padding:9px 15px;border:1px solid #bfdbfe;border-radius:8px;color:#fff;background:#2563eb;font:inherit;font-weight:700;cursor:pointer}.upload-actions button:disabled,.toolbar button:disabled{opacity:.55}.toolbar{justify-content:space-between;gap:20px;margin-bottom:18px}.toolbar>div{gap:12px}.toolbar span{color:#64748b}.toolbar form{gap:8px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid #e2e8f0;text-align:left}th{color:#475569;background:#f8fafc;font-size:13px}td small{display:block;margin-top:4px;color:#64748b}.download{padding:7px 12px;color:#1d4ed8;background:#fff}.empty{text-align:center;color:#64748b}@media(max-width:700px){.page{padding:24px 14px}.page-header,.toolbar,.upload-actions{align-items:stretch;flex-direction:column}.form-grid{grid-template-columns:1fr}.toolbar form{width:100%}}
</style>
