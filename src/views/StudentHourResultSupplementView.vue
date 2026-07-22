<script setup>
import { computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AttachmentNotice from '../components/AttachmentNotice.vue'
import StatusTag from '../components/StatusTag.vue'
import { canSupplementResult, getApplications, supplementApplicationResult } from '../mock/applications.js'

const route = useRoute(); const router = useRouter()
const currentUser = { id: 'stu001', studentId: '2024001' }
const application = computed(() => getApplications().find((item) => item.id === route.params.id && item.currentUserId === currentUser.id))
const allowed = computed(() => canSupplementResult(application.value))
const form = reactive({ description: '', resultFiles: [], proofFiles: [] })
function nowText(){return new Date().toLocaleString('zh-CN',{hour12:false}).replaceAll('/','-')}
function sizeText(bytes){if(bytes>=1048576)return`${(bytes/1048576).toFixed(2)} MB`;if(bytes>=1024)return`${(bytes/1024).toFixed(2)} KB`;return`${bytes} B`}
function selectFiles(event,target,category){Array.from(event.target.files||[]).forEach((file,index)=>target.push({id:`SUP-${Date.now()}-${index}`,name:file.name,type:file.type||'未知类型',size:sizeText(file.size),uploadedAt:nowText(),mockUrl:URL.createObjectURL(file),category}));event.target.value=''}
function removeFile(target,id){const file=target.find((item)=>item.id===id);if(file?.mockUrl)URL.revokeObjectURL(file.mockUrl);const index=target.findIndex((item)=>item.id===id);if(index>=0)target.splice(index,1)}
function preview(){window.alert('当前为 Mock 附件预览，真实预览需后端文件服务支持。')}
function download(){window.alert('当前为 Mock 附件下载，真实下载需后端文件服务支持。')}
function back(){router.push(application.value?`/student/hour-progress/${application.value.id}`:'/student/hour-progress')}
function submit(){if(!allowed.value)return window.alert('当前申请不支持补交成果。');if(!form.description.trim())return window.alert('请填写成果说明。');if(!form.resultFiles.length)return window.alert('请至少上传一项成果材料。');const updated=supplementApplicationResult(application.value.id,{resultDescription:form.description,resultMaterials:form.resultFiles,proofMaterials:form.proofFiles});if(!updated)return window.alert('补交成果失败，请检查当前申请状态。');window.alert('成果已补交，等待指导老师再次确认。');router.push('/student/hour-progress')}
</script>

<template><main class="page"><div class="content"><template v-if="application">
  <header><div><p class="eyebrow">S503 · RESULT SUPPLEMENT</p><h1>补交成果</h1><p>{{ application.title }} · {{ application.id }}</p></div><StatusTag :status="application.status" /></header>
  <section v-if="!allowed" class="warning">当前申请不支持补交成果。</section>
  <section class="card"><h2>原申请基本信息</h2><dl class="grid"><div><dt>申请名称</dt><dd>{{ application.title }}</dd></div><div><dt>申请类型</dt><dd>{{ application.applyTypeText }}</dd></div><div><dt>主指导老师</dt><dd>{{ application.mainAdvisor?.name || '--' }}</dd></div><div><dt>当前状态</dt><dd><StatusTag :status="application.status" /></dd></div><div><dt>原预计成果提交时间</dt><dd>{{ application.expectedResultDate || '--' }}</dd></div><div><dt>已补交次数</dt><dd>{{ application.supplementCount || 0 }} / 1</dd></div><div class="wide"><dt>原申请说明</dt><dd>{{ application.description || application.title }}</dd></div></dl></section>
  <section class="card"><h2>成果说明</h2><textarea v-model="form.description" rows="6" :disabled="!allowed" placeholder="请说明成果内容、完成情况和补充原因。"></textarea></section>
  <section class="card"><h2>成果材料</h2><AttachmentNotice title="成果材料" description="请选择成果报告、作品、数据文件或其他成果证明。当前为 Mock 上传。" :required="true" :accept-types="['PDF','Word','Excel','PPT','图片','压缩包']" /><input type="file" multiple :disabled="!allowed" @change="selectFiles($event,form.resultFiles,'result')" /><div class="files"><article v-for="file in form.resultFiles" :key="file.id"><div><strong>{{ file.name }}</strong><small>{{ file.type }} · {{ file.size }} · {{ file.uploadedAt }}</small></div><div><button type="button" @click="preview">预览</button><button type="button" @click="download">下载</button><button type="button" class="delete" @click="removeFile(form.resultFiles,file.id)">删除</button></div></article></div></section>
  <section class="card"><h2>证明材料</h2><AttachmentNotice title="证明材料" description="可选填过程记录、参与证明或其他辅助材料。" :required="false" :accept-types="['PDF','Word','图片']" /><input type="file" multiple :disabled="!allowed" @change="selectFiles($event,form.proofFiles,'proof')" /><div class="files"><article v-for="file in form.proofFiles" :key="file.id"><div><strong>{{ file.name }}</strong><small>{{ file.type }} · {{ file.size }} · {{ file.uploadedAt }}</small></div><div><button type="button" @click="preview">预览</button><button type="button" @click="download">下载</button><button type="button" class="delete" @click="removeFile(form.proofFiles,file.id)">删除</button></div></article></div></section>
  <div class="actions"><button type="button" @click="back">返回</button><button type="button" class="submit" :disabled="!allowed" @click="submit">提交补交成果</button></div>
</template><section v-else class="card empty">申请不存在或不属于当前学生。<button type="button" @click="back">返回</button></section></div></main></template>

<style scoped>
.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,980px);margin:auto}header{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}h1{margin:0}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800;letter-spacing:.12em}header p{color:#64748b}.warning{margin-bottom:18px;padding:15px;border-radius:10px;color:#b91c1c;background:#fee2e2}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin:0 0 18px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:0}.wide{grid-column:1/-1}dt{color:#64748b;font-size:13px}dd{margin:5px 0 0;font-weight:600;line-height:1.7}textarea,input[type=file]{width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:9px;font:inherit}input[type=file]{margin-top:16px}.files{display:grid;gap:10px;margin-top:14px}.files article{display:flex;justify-content:space-between;gap:14px;padding:13px;border:1px solid #e2e8f0;border-radius:9px;background:#f8fafc}.files small{display:block;margin-top:5px;color:#64748b}.files article>div:last-child{display:flex;gap:8px}.files button,.actions button,.empty button{padding:8px 11px;border:1px solid #bfdbfe;border-radius:8px;color:#2563eb;background:#fff;font:inherit;font-weight:700}.files .delete{color:#b91c1c;border-color:#fecaca}.actions{display:flex;justify-content:flex-end;gap:10px}.actions button{padding:10px 18px}.actions .submit{border:0;color:#fff;background:#2563eb}.actions button:disabled{opacity:.5}.empty{text-align:center;color:#64748b}@media(max-width:650px){.page{padding:24px 14px}header,.files article{flex-direction:column}.grid{grid-template-columns:1fr}.wide{grid-column:auto}.actions{flex-wrap:wrap}}
</style>
