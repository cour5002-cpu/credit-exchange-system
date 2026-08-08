import { adaptAttachment } from './taskAdapter.js'
import { adaptStudent } from './userAdapter.js'
import { adaptApplication } from './applicationAdapter.js'

export function adaptAppeal(item) {
  if (!item) return null
  const originalApplication = item.original_application ?? item.target ?? null
  const applicationId = item.hour_application_id ?? originalApplication?.id ?? item.target_id
  const attachments = item.attachments ?? item.appeal_materials ?? (item.attachment_ids ?? []).map((attachment) => (
    typeof attachment === 'object' && attachment !== null ? attachment : { id: attachment }
  ))
  return {
    id: item.id,
    appealId: item.appeal_id ?? item.id,
    appealNo: item.appeal_no,
    targetType: item.target_type,
    applicationId,
    hourApplicationId: applicationId,
    targetId: item.target_id ?? applicationId,
    applicationType: item.application_type ?? originalApplication?.application_type,
    applicationTitle: item.target?.title ?? item.target_title ?? `${item.target_type === 'credit_exchange' ? '学分兑换' : '课时申请'} #${item.target_id}`,
    student: adaptStudent(item.student),
    studentId: item.student?.student_no,
    studentName: item.student?.name,
    appealReason: item.reason,
    status: item.status,
    reopenStage: item.reopen_stage ?? null,
    targetStatus: item.target_status ?? originalApplication?.status,
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
    originalApplication: originalApplication ? adaptApplication(originalApplication) : null,
    target: originalApplication ? adaptApplication(originalApplication) : null,
    appealMaterials: attachments.map(adaptAttachment).filter(Boolean),
  }
}

export function adaptAppealEnvelope(payload) {
  if (!payload) return null
  const appeal = payload.appeal ?? payload
  return adaptAppeal({
    ...appeal,
    target: payload.target ?? appeal.target,
    original_application: payload.original_application ?? appeal.original_application,
    hour_application_id: payload.hour_application_id ?? appeal.hour_application_id,
    target_status: payload.target_status ?? appeal.target_status,
    application_type: payload.application_type ?? appeal.application_type,
    attachments: payload.attachments ?? appeal.attachments ?? payload.appeal_materials ?? appeal.appeal_materials,
    attachment_ids: payload.attachment_ids ?? appeal.attachment_ids,
  })
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
