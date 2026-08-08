<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { downloadRuleFile, getRuleFileBlob } from '../api/ruleFileApi.js'
import { getApiErrorMessage } from '../utils/apiFeedback.js'

const props = defineProps({ item: { type: Object, required: true }, showName: { type: Boolean, default: true } })
const previewOpen = ref(false)
const loading = ref(false)
const previewUrl = ref('')
const fileName = computed(() => props.item.attachment?.file_name || props.item.title || '规则文件')
const mimeType = computed(() => props.item.attachment?.mime_type || '未知类型')
const previewType = computed(() => {
  const mime = mimeType.value.toLowerCase()
  const name = fileName.value.toLowerCase()
  if (mime.startsWith('image/') || /\.(png|jpe?g|gif|webp|bmp|svg)$/.test(name)) return 'image'
  if (mime === 'application/pdf' || name.endsWith('.pdf')) return 'pdf'
  if (/word|officedocument\.wordprocessingml/.test(mime) || /\.docx?$/.test(name)) return 'document'
  if (/excel|spreadsheetml/.test(mime) || /\.xlsx?$/.test(name)) return 'spreadsheet'
  return 'file'
})

function closePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  previewOpen.value = false
  loading.value = false
}

async function preview() {
  previewOpen.value = true
  if (!['image', 'pdf'].includes(previewType.value)) return
  loading.value = true
  try {
    const { blob } = await getRuleFileBlob(props.item.id)
    previewUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    closePreview()
    window.alert(getApiErrorMessage(error, '规则文件预览失败'))
  } finally {
    loading.value = false
  }
}

async function download() {
  try { await downloadRuleFile(props.item.id, fileName.value) }
  catch (error) { window.alert(getApiErrorMessage(error, '规则文件下载失败')) }
}
onBeforeUnmount(closePreview)
</script>

<template>
  <div class="viewer">
    <div v-if="showName" class="file-info"><strong>{{ item.title }}</strong><small>{{ fileName }} · {{ mimeType }}</small></div>
    <div class="file-actions"><button type="button" @click="preview">预览</button><button type="button" @click="download">下载</button></div>
    <Teleport to="body"><div v-if="previewOpen" class="overlay" @click.self="closePreview"><section class="dialog"><header><div><strong>{{ item.title }}</strong><small>{{ fileName }} · {{ mimeType }}</small></div><button type="button" @click="closePreview">关闭</button></header><div class="content"><p v-if="loading">正在加载预览...</p><img v-else-if="previewType === 'image' && previewUrl" :src="previewUrl" :alt="item.title" /><iframe v-else-if="previewType === 'pdf' && previewUrl" :src="previewUrl" :title="item.title" /><p v-else>{{ previewType === 'document' ? 'Word 文档' : previewType === 'spreadsheet' ? 'Excel 工作簿' : '该类型文件' }}不支持在线预览，请下载后查看。</p></div><footer><button type="button" @click="download">下载文件</button></footer></section></div></Teleport>
  </div>
</template>

<style scoped>
.viewer{display:flex;width:100%;align-items:center;justify-content:space-between;gap:16px}.file-info{min-width:0}.file-info strong,.file-info small{display:block}.file-info small{margin-top:4px;color:#64748b}.file-actions{display:flex;gap:8px}.viewer button{flex:none;padding:7px 12px;border:1px solid #93c5fd;border-radius:8px;color:#1d4ed8;background:#fff;font:inherit;font-weight:700;cursor:pointer}.overlay{position:fixed;inset:0;z-index:10000;display:grid;padding:24px;background:rgba(15,23,42,.72);place-items:center}.dialog{display:flex;width:min(100%,1000px);height:min(88vh,800px);overflow:hidden;border-radius:14px;background:#fff;box-shadow:0 24px 60px rgba(15,23,42,.35);flex-direction:column}.dialog header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 20px;border-bottom:1px solid #e2e8f0}.dialog header small{display:block;margin-top:4px;color:#64748b}.content{display:grid;min-height:0;padding:18px;overflow:auto;background:#f8fafc;place-items:center;flex:1}.content img{display:block;max-width:100%;max-height:100%;object-fit:contain}.content iframe{width:100%;height:100%;min-height:520px;border:0;background:#fff}.dialog footer{display:flex;justify-content:flex-end;padding:12px 20px;border-top:1px solid #e2e8f0}@media(max-width:620px){.viewer{align-items:flex-start;flex-direction:column}}
</style>
