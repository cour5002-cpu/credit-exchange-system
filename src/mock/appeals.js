import { getApplications, updateApplicationByAppealResult } from './applications.js'

export const APPEAL_STATUS = Object.freeze({
  PENDING_ADMIN:'pending_admin_review', ADMIN_REJECTED:'completed', PENDING_ADVISOR_CONFIRMATION:'processing', PENDING_REVIEW_ASSIGNMENT:'processing',
  PENDING_RE_REVIEW:'processing', RE_REVIEW_APPROVED:'processing', RE_REVIEW_REJECTED:'completed', FINAL_CONFIRMED:'completed',
})
const appeals=[]
function nowText(){const date=new Date();const pad=(value)=>String(value).padStart(2,'0');return`${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`}
const activeStatuses=new Set([APPEAL_STATUS.PENDING_ADMIN,APPEAL_STATUS.PENDING_ADVISOR_CONFIRMATION])
const appealableStatuses=new Set(['final_approved','final_rejected','advisor_rejected','reviewer_rejected','rejected','modified_approved','reviewer_modified_approved'])
export function getAppeals(){return appeals}
export function getAppealById(appealId){return appeals.find((appeal)=>appeal.appealId===appealId)}
export function getStudentAppeals(studentId){return appeals.filter((appeal)=>appeal.studentId===studentId)}
export function hasActiveAppeal(applicationId,studentId){return appeals.some((appeal)=>appeal.applicationId===applicationId&&appeal.studentId===studentId&&activeStatuses.has(appeal.status))}
export function isApplicationAppealable(application,studentId){return Boolean(application&&application.studentId===studentId&&!hasActiveAppeal(application.id,studentId)&&(appealableStatuses.has(application.status)||(application.status==='final_approved'&&application.reviewStatus==='modified_approved')))}
export function getAppealableApplications(studentId){return getApplications().filter((application)=>isApplicationAppealable(application,studentId))}
export function addAppeal(data){const application=getApplications().find((item)=>item.id===data?.applicationId);if(!application||!isApplicationAppealable(application,data.studentId)||!data.appealReason?.trim())return null;const appeal={appealId:data.appealId||`APL-${Date.now()}`,applicationId:application.id,applicationTitle:application.title,studentId:data.studentId,studentName:data.studentName||application.studentName,originalStatus:application.status,originalFinalHours:application.recognizedHours??application.requestedHours,originalComment:application.finalComment||application.reviewComment||application.advisorComment||'',appealReason:data.appealReason.trim(),appealMaterials:(data.appealMaterials||[]).map((file)=>({...file})),submitTime:data.submitTime||nowText(),status:APPEAL_STATUS.PENDING_ADMIN,adminComment:'',adminHandleTime:'',reviewTeacherId:'',reviewTeacherName:'',reviewResult:'',finalResult:'',timeline:[{title:'学生提交申诉',time:data.submitTime||nowText(),status:'completed'},{title:'等待管理员处理',time:'',status:'current'}]};appeals.push(appeal);return appeal}

export function getAdminPendingAppeals(){return appeals.filter((appeal)=>appeal.status===APPEAL_STATUS.PENDING_ADMIN)}
function completeCurrentTimeline(appeal){appeal.timeline=(appeal.timeline||[]).map((step)=>step.status==='current'?{...step,status:'completed',time:step.time||nowText()}:step)}
export function acceptAppeal(appealId,comment=''){const appeal=getAppealById(appealId);if(!appeal||appeal.status!==APPEAL_STATUS.PENDING_ADMIN)return null;const handledAt=nowText();completeCurrentTimeline(appeal);appeal.status=APPEAL_STATUS.PENDING_ADVISOR_CONFIRMATION;appeal.reopenStage='pending_advisor_confirmation';appeal.adminComment=comment.trim();appeal.adminHandleTime=handledAt;appeal.timeline.push({title:'管理员已受理申诉，等待指导老师再次确认。',time:handledAt,status:'current'});return appeal}
export function rejectAppealByAdmin(appealId,comment=''){const appeal=getAppealById(appealId);if(!appeal||appeal.status!==APPEAL_STATUS.PENDING_ADMIN||!comment.trim())return null;const handledAt=nowText();completeCurrentTimeline(appeal);appeal.status=APPEAL_STATUS.ADMIN_REJECTED;appeal.adminComment=comment.trim();appeal.adminHandleTime=handledAt;appeal.finalResult='appeal_rejected';appeal.timeline.push({title:'管理员不受理该申诉。',time:handledAt,status:'completed'});return appeal}

export function getPendingReviewAssignmentAppeals(){return appeals.filter((appeal)=>appeal.status===APPEAL_STATUS.PENDING_REVIEW_ASSIGNMENT&&appeal.reopenStage==='pending_assignment')}
export function getAdvisorPendingAppealConfirmations(){return appeals.filter((appeal)=>appeal.status===APPEAL_STATUS.PENDING_ADVISOR_CONFIRMATION&&appeal.reopenStage==='pending_advisor_confirmation')}
export function reconfirmAppeal(appealId,decision,comment=''){const appeal=getAppealById(appealId);if(!appeal||appeal.reopenStage!=='pending_advisor_confirmation'||!['approve','reject'].includes(decision))return null;completeCurrentTimeline(appeal);if(decision==='reject'){appeal.status=APPEAL_STATUS.FINAL_CONFIRMED;appeal.reopenStage='completed';appeal.finalResult='rejected';appeal.timeline.push({title:'指导老师再次确认驳回，申诉处理完成。',time:nowText(),status:'completed'})}else{appeal.status=APPEAL_STATUS.PENDING_REVIEW_ASSIGNMENT;appeal.reopenStage='pending_assignment';appeal.timeline.push({title:'指导老师再次确认通过，等待管理员分配复审老师。',time:nowText(),status:'current'})}appeal.advisorReconfirmComment=comment.trim();return appeal}
export function assignReviewTeacher(appealId,teacher,admin={id:'ADMIN001',name:'系统管理员'}){const appeal=getAppealById(appealId);const teacherId=teacher?.reviewerId||teacher?.id;const teacherName=teacher?.reviewerName||teacher?.name;if(!appeal||appeal.reopenStage!=='pending_assignment'||!teacherId||!teacherName)return null;const assignedAt=nowText();completeCurrentTimeline(appeal);appeal.status=APPEAL_STATUS.PENDING_RE_REVIEW;appeal.reopenStage='pending_reviewer_review';appeal.reviewTeacherId=teacherId;appeal.reviewTeacherName=teacherName;appeal.reviewAssignTime=assignedAt;appeal.assignAdminId=admin.id;appeal.assignAdminName=admin.name;appeal.timeline.push({title:`管理员已分配复审老师：${teacherName}。`,time:assignedAt,status:'current'});return appeal}
export function getReviewerPendingAppeals(reviewTeacherId){return appeals.filter((appeal)=>appeal.reopenStage==='pending_reviewer_review'&&appeal.reviewTeacherId===reviewTeacherId)}
export function approveAppealReview(appealId,reviewHours,comment=''){const appeal=getAppealById(appealId);const hours=Number(reviewHours);if(!appeal||appeal.reopenStage!=='pending_reviewer_review'||!Number.isFinite(hours)||hours<0||!comment.trim())return null;const reviewedAt=nowText();completeCurrentTimeline(appeal);appeal.status=APPEAL_STATUS.RE_REVIEW_APPROVED;appeal.reopenStage='pending_admin_final';appeal.reviewResult='approved';appeal.reviewHours=hours;appeal.reviewComment=comment.trim();appeal.reviewTime=reviewedAt;appeal.timeline.push({title:'审核老师复审通过，等待管理员最终确认。',time:reviewedAt,status:'current'});return appeal}
export function rejectAppealReview(appealId,comment=''){const appeal=getAppealById(appealId);if(!appeal||appeal.reopenStage!=='pending_reviewer_review'||!comment.trim())return null;const reviewedAt=nowText();completeCurrentTimeline(appeal);appeal.status=APPEAL_STATUS.RE_REVIEW_REJECTED;appeal.reopenStage='completed';appeal.reviewResult='rejected';appeal.reviewComment=comment.trim();appeal.reviewTime=reviewedAt;appeal.timeline.push({title:'审核老师复审驳回，申诉处理完成。',time:reviewedAt,status:'completed'});return appeal}
export function getAdminPendingAppealFinalConfirm(){return appeals.filter((appeal)=>appeal.reopenStage==='pending_admin_final')}
export function finalConfirmAppeal(appealId,comment=''){
  const appeal=getAppealById(appealId)
  if(!appeal||appeal.reopenStage!=='pending_admin_final')return null
  const approved=appeal.status===APPEAL_STATUS.RE_REVIEW_APPROVED&&appeal.reviewResult==='approved'
  if(approved&&!updateApplicationByAppealResult(appeal.applicationId,appeal))return null
  const confirmedAt=nowText()
  completeCurrentTimeline(appeal)
  appeal.status=APPEAL_STATUS.FINAL_CONFIRMED
  appeal.reopenStage='completed'
  appeal.finalResult=approved?'approved':'rejected'
  appeal.finalAdminComment=comment.trim()
  appeal.finalConfirmTime=confirmedAt
  appeal.timeline.push({title:approved?'管理员最终确认申诉复审通过，课时结果已更新。':'管理员最终确认申诉复审驳回，原课时结果保持不变。',time:confirmedAt,status:'completed'})
  return appeal
}
