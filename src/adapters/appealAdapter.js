import { adaptAttachment } from './taskAdapter.js'
import { adaptStudent } from './userAdapter.js'

export function adaptAppeal(item) {
  if (!item) return null
  return {
    id: item.id,
    appealId: item.id,
    appealNo: item.appeal_no,
    targetType: item.target_type,
    applicationId: item.target_id,
    student: adaptStudent(item.student),
    studentId: item.student?.student_no,
    studentName: item.student?.name,
    appealReason: item.reason,
    status: item.status,
    reopenStage: item.reopen_stage ?? null,
    submitTime: item.submitted_at,
    appealMaterials: (item.attachments ?? []).map(adaptAttachment),
  }
}

export const toAppealPayload = (form) => ({
  target_type: form.targetType ?? 'hour_application',
  target_id: form.targetId ?? form.applicationId,
  reason: form.appealReason,
  attachment_ids: form.attachmentIds ?? [],
})
