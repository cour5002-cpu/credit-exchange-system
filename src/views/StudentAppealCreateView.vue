<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatusTag from '../components/StatusTag.vue'
import { getAppealableTarget, submitAppeal } from '../api/appealApi.js'
import { getStudentApplications } from '../api/applicationApi.js'
import { uploadAttachment } from '../api/fileApi.js'
const route=useRoute();const router=useRouter();const targetType=ref(String(route.query.targetType||'hour_application'))
const form=reactive({applicationId:Number(route.query.applicationId||route.query.targetId||0),reason:'',files:[],attachmentIds:[]});const applications=ref([]);const canAppeal=ref(false)
const selected=computed(()=>applications.value.find((item)=>Number(item.id)===Number(form.applicationId)))
async function loadAppealableApplications(){
  try{
    if(form.applicationId){
      const data=await getAppealableTarget(targetType.value,form.applicationId)
      canAppeal.value=Boolean(data?.can_appeal)
      applications.value=data?.can_appeal&&data?.target?[data.target]:[]
      if(!canAppeal.value)window.alert(data?.reason||'该业务当前不可申诉')
      return
    }
    const candidates=[]
    let page=1;let pages=1
    do{
      const payload=await getStudentApplications({page,page_size:100})
      candidates.push(...(payload?.items??[]).filter(item=>['reviewer_rejected','final_rejected'].includes(item.status)))
      pages=Number(payload?.pages)||1;page+=1
    }while(page<=pages)
    const checks=await Promise.allSettled(candidates.map(item=>getAppealableTarget('hour_application',item.id)))
    applications.value=checks.filter(result=>result.status==='fulfilled'&&result.value?.can_appeal&&result.value?.target).map(result=>result.value.target)
    canAppeal.value=applications.value.length>0
  }catch(error){window.alert(error?.message||'可申诉课时申请加载失败')}
}
onMounted(loadAppealableApplications)
function nowText(){return new Date().toLocaleString('zh-CN',{hour12:false}).replaceAll('/','-')};function sizeText(bytes){if(bytes>=1048576)return`${(bytes/1048576).toFixed(2)} MB`;if(bytes>=1024)return`${(bytes/1024).toFixed(2)} KB`;return`${bytes} B`}
async function selectFiles(event){for(const file of Array.from(event.target.files||[])){try{const uploaded=await uploadAttachment(file,'appeal');form.files.push({...uploaded.attachment,id:uploaded.id,name:file.name,type:file.type||'未知类型',size:sizeText(file.size),uploadedAt:nowText()});form.attachmentIds.push(uploaded.id)}catch(error){window.alert(error?.message||'申诉附件上传失败')}}event.target.value=''}
function removeFile(id){const index=form.files.findIndex((item)=>item.id===id);if(index>=0)form.files.splice(index,1);form.attachmentIds=form.attachmentIds.filter(item=>item!==id)}
async function submit(){if(!selected.value||!canAppeal.value)return window.alert('当前业务不可申诉。');if(!form.reason.trim())return window.alert('请填写申诉原因。');if(!form.attachmentIds.length)return window.alert('请上传申诉证明材料。');try{await submitAppeal({target_type:targetType.value,target_id:Number(form.applicationId),reason:form.reason.trim(),attachment_ids:form.attachmentIds});window.alert('申诉已提交，等待管理员处理。');router.push('/student/appeals')}catch(error){window.alert(error?.message||'申诉提交失败')}}
</script>
<template><main class="page"><div class="content"><header><div><p class="eyebrow">S701 · CREATE APPEAL</p><h1>发起申诉</h1><p>选择已有明确处理结果的课时申请。</p></div><RouterLink to="/student/feedback">返回问题反馈</RouterLink></header><section class="card"><label>可申诉申请</label><select v-model="form.applicationId"><option value="">请选择课时申请</option><option v-for="item in applications" :key="item.id" :value="item.id">{{ item.title }} · {{ item.id }}</option></select><p v-if="!applications.length" class="muted">暂无可申诉的课时申请。</p></section><section v-if="selected" class="card"><h2>原申请信息</h2><dl class="grid"><div><dt>申请名称</dt><dd>{{ selected.title }}</dd></div><div><dt>申请状态</dt><dd><StatusTag :status="selected.status" /></dd></div><div><dt>原认定课时</dt><dd>{{ selected.recognizedHours??selected.requestedHours }} 课时</dd></div><div><dt>原处理意见</dt><dd>{{ selected.finalComment||selected.reviewComment||selected.advisorComment||'--' }}</dd></div></dl></section><section class="card"><h2>申诉原因</h2><textarea v-model="form.reason" rows="6" placeholder="请详细说明申诉理由。"></textarea></section><section class="card"><h2>申诉材料</h2><input type="file" multiple @change="selectFiles" /><div class="files"><article v-for="file in form.files" :key="file.id"><div><strong>{{ file.name }}</strong><small>{{ file.type }} · {{ file.size }} · {{ file.uploadedAt }}</small></div><button @click="removeFile(file.id)">删除</button></article></div></section><div class="actions"><RouterLink to="/student/feedback">返回</RouterLink><button @click="submit">提交申诉</button></div></div></main></template>
<style scoped>.page{min-height:100vh;padding:40px 24px;background:#f3f6fb}.content{width:min(100%,900px);margin:auto}header{display:flex;justify-content:space-between;margin-bottom:20px}h1{margin:0}.eyebrow{margin:0 0 6px;color:#2563eb;font-size:12px;font-weight:800}.card{margin-bottom:18px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.card h2{margin-top:0}.card label{display:block;margin-bottom:8px;font-weight:700}select,textarea,input[type=file]{width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:9px;font:inherit}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}dt,.muted{color:#64748b}dd{margin:5px 0 0;font-weight:600}.files{display:grid;gap:9px;margin-top:14px}.files article{display:flex;justify-content:space-between;padding:13px;background:#f8fafc}.files small{display:block;color:#64748b}.files button{color:#b91c1c}.actions{display:flex;justify-content:flex-end;gap:10px}.actions a,.actions button,header a{padding:10px 16px;border:1px solid #cbd5e1;border-radius:9px;color:#2563eb;background:#fff;font-weight:700;text-decoration:none}.actions button{color:#fff;background:#2563eb}@media(max-width:650px){.grid{grid-template-columns:1fr}}</style>
