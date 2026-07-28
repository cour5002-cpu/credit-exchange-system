import { adaptAttachment } from './taskAdapter.js'
import { adaptStudent } from './userAdapter.js'
import { adaptApplication } from './applicationAdapter.js'

export function adaptAppeal(item) {
  if (!item) return null
  return {
    id: item.id,
    appealId: item.appeal_id ?? item.id,
    appealNo: item.appeal_no,
    targetType: item.target_type,
    applicationId: item.target_id,
    targetId: item.target_id,
    applicationTitle: item.target?.title ?? item.target_title ?? `${item.target_type === 'credit_exchange' ? '学分兑换' : '课时申请'} #${item.target_id}`,
    student: adaptStudent(item.student),
    studentId: item.student?.student_no,
    studentName: item.student?.name,
    appealReason: item.reason,
    status: item.status,
    reopenStage: item.reopen_stage ?? null,
    submitTime: item.submitted_at,
    adminComment: item.admin_advice,
    adminHandleTime: item.reviewed_at,
    originalStatus: item.target?.status ?? item.original_status,
    originalFinalHours: item.target?.final_hours ?? item.target?.total_hours ?? item.original_final_hours,
    originalComment: item.target?.final_comment ?? item.original_comment,
    reviewTeacherId: item.reviewer?.id ?? item.reviewer_teacher_id,
    reviewTeacherName: item.reviewer?.name ?? item.reviewer_name,
    reviewResult: item.review_result,
    reviewHours: item.reviewer_suggested_hours ?? item.review_hours,
    reviewComment: item.review_comment,
    reviewTime: item.reviewed_at,
    reviewerTeacherId: item.reviewer_teacher_id ?? item.reviewer?.id,
    originalApplication: item.original_application ? adaptApplication(item.original_application) : (item.target ? adaptApplication(item.target) : null),
    target: item.target ? adaptApplication(item.target) : null,
    appealMaterials: (item.attachments ?? []).map(adaptAttachment),
  }
}

export function adaptAppealEnvelope(payload) {
  if (!payload) return null
  const appeal = payload.appeal ?? payload
  return adaptAppeal({ ...appeal, target: payload.target ?? appeal.target, attachments: payload.attachments ?? appeal.attachments })
}

export const adaptAppealList = (payload) => (
  Array.isArray(payload) ? payload : payload?.items ?? []
).map(adaptAppeal).filter(Boolean)

export const toAppealPayload = (form) => ({
  target_type: form.targetType ?? 'hour_application',
  target_id: form.targetId ?? form.applicationId,
  reason: form.appealReason,
  attachment_ids: form.attachmentIds ?? [],
})
