<script setup>
import { computed, ref } from 'vue'
import { getRuleFiles } from '../api/ruleFileApi.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'
import RuleFileViewer from './RuleFileViewer.vue'

const props = defineProps({
  ruleType: { type: String, required: true },
  title: { type: String, default: '相关规则文件' },
  description: { type: String, default: '请在操作前阅读相关规则文件。' },
})
const showRuleFiles = ref(false)
const loaded = ref(false)
const items = ref([])
const loading = ref(false)
const loadError = ref('')
const filteredItems = computed(() => items.value.filter((item) => item.rule_type === props.ruleType))

async function toggleRuleFiles() {
  showRuleFiles.value = !showRuleFiles.value
  if (!showRuleFiles.value || loaded.value) return
  loading.value = true
  loadError.value = ''
  try {
    const payload = await getRuleFiles()
    items.value = Array.isArray(payload) ? payload : payload?.items ?? []
    loaded.value = true
  } catch (error) {
    loadError.value = getApiErrorMessage(error, '规则文件加载失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="rule-panel">
    <button class="toggle" type="button" :aria-expanded="showRuleFiles" @click="toggleRuleFiles">{{ showRuleFiles ? '收起规则文件' : '查看规则文件' }}</button>
    <div v-if="showRuleFiles" class="panel-content">
      <header><h2>{{ title }}</h2><p>{{ description }}</p></header>
      <p v-if="loading" class="state">正在加载规则文件...</p>
      <p v-else-if="loadError" class="state state--error">{{ loadError }}</p>
      <div v-else-if="filteredItems.length" class="rule-list"><article v-for="item in filteredItems" :key="item.id"><RuleFileViewer :item="item" /></article></div>
      <p v-else class="state">暂无相关规则文件</p>
    </div>
  </section>
</template>

<style scoped>
.rule-panel{margin-bottom:18px;padding:16px 18px;border:1px solid #bfdbfe;border-radius:14px;background:#eff6ff}.toggle{padding:9px 15px;border:1px solid #93c5fd;border-radius:8px;color:#1d4ed8;background:#fff;font:inherit;font-weight:700;cursor:pointer}.panel-content{margin-top:16px;padding-top:16px;border-top:1px solid #bfdbfe}.panel-content h2{margin:0;color:#1e3a8a;font-size:18px}.panel-content header p{margin:6px 0 0;color:#475569}.rule-list{display:grid;gap:10px;margin-top:16px}.rule-list article{padding:13px 14px;border:1px solid #dbeafe;border-radius:9px;background:#fff}.state{margin:14px 0 0;color:#64748b}.state--error{color:#b91c1c}
</style>
