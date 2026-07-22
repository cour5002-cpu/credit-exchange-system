import { getApplications } from './applications.js'

export const APPEAL_STATUS = Object.freeze({
  PENDING_ADMIN:'pending_admin', ADMIN_REJECTED:'admin_rejected', PENDING_REVIEW_ASSIGNMENT:'pending_review_assignment',
  PENDING_RE_REVIEW:'pending_re_review', RE_REVIEW_APPROVED:'re_review_approved', RE_REVIEW_REJECTED:'re_review_rejected', FINAL_CONFIRMED:'final_confirmed',
})
const appeals=[]
function nowText(){const date=new Date();const pad=(value)=>String(value).padStart(2,'0');return`${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`}
const activeStatuses=new Set([APPEAL_STATUS.PENDING_ADMIN,APPEAL_STATUS.PENDING_REVIEW_ASSIGNMENT,APPEAL_STATUS.PENDING_RE_REVIEW,APPEAL_STATUS.RE_REVIEW_APPROVED])
const appealableStatuses=new Set(['final_approved','final_rejected','advisor_rejected','reviewer_rejected','rejected','modified_approved','reviewer_modified_approved'])
export function getAppeals(){return appeals}
export function getAppealById(appealId){return appeals.find((appeal)=>appeal.appealId===appealId)}
export function getStudentAppeals(studentId){return appeals.filter((appeal)=>appeal.studentId===studentId)}
export function hasActiveAppeal(applicationId,studentId){return appeals.some((appeal)=>appeal.applicationId===applicationId&&appeal.studentId===studentId&&activeStatuses.has(appeal.status))}
export function isApplicationAppealable(application,studentId){return Boolean(application&&application.studentId===studentId&&!hasActiveAppeal(application.id,studentId)&&(appealableStatuses.has(application.status)||(application.status==='final_approved'&&application.reviewStatus==='modified_approved')))}
export function getAppealableApplications(studentId){return getApplications().filter((application)=>isApplicationAppealable(application,studentId))}
export function addAppeal(data){const application=getApplications().find((item)=>item.id===data?.applicationId);if(!application||!isApplicationAppealable(application,data.studentId)||!data.appealReason?.trim())return null;const appeal={appealId:data.appealId||`APL-${Date.now()}`,applicationId:application.id,applicationTitle:application.title,studentId:data.studentId,studentName:data.studentName||application.studentName,originalStatus:application.status,originalFinalHours:application.recognizedHours??application.requestedHours,originalComment:application.finalComment||application.reviewComment||application.advisorComment||'',appealReason:data.appealReason.trim(),appealMaterials:(data.appealMaterials||[]).map((file)=>({...file})),submitTime:data.submitTime||nowText(),status:APPEAL_STATUS.PENDING_ADMIN,adminComment:'',adminHandleTime:'',reviewTeacherId:'',reviewTeacherName:'',reviewResult:'',finalResult:'',timeline:[{title:'学生提交申诉',time:data.submitTime||nowText(),status:'completed'},{title:'等待管理员处理',time:'',status:'current'}]};appeals.push(appeal);return appeal}
