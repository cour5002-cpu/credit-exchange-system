import { adaptAttachment } from './taskAdapter.js'

export const COMPLAINT_CATEGORY_TEXT = Object.freeze({
  personnel_behavior: '人员行为',
  service_quality: '服务质量',
  process_violation: '流程违规',
  other: '其他问题',
})

export const COMPLAINT_STATUS_TEXT = Object.freeze({
  submitted: '已提交',
  processing: '处理中',
  resolved: '已处理',
})

export const COMPLAINT_HANDLING_RESULT_TEXT = Object.freeze({
  substantiated: '投诉成立',
  partially_substantiated: '部分成立',
  unsubstantiated: '投诉不成立',
  transferred: '已转交其他渠道',
  other: '其他处理结果',
})

export function adaptComplaint(item) {
  if (!item) return null
  const attachments = (
    item.attachments ?? (item.attachment_ids ?? []).map((id) => ({ id }))
  ).map(adaptAttachment).filter(Boolean)
  const category = item.category ?? item.complaint_category ?? item.complaint_type
  const status = item.status
  const handlingResult = item.handling_result ?? item.handlingResult
  const content = item.content ?? item.complaintContent
  const createdAt = item.created_at ?? item.createdAt
  const rawSubmitter = item.submitter
  const submitter = rawSubmitter ? {
    ...rawSubmitter,
    name: rawSubmitter.name,
    studentNo: rawSubmitter.student_no ?? rawSubmitter.studentNo,
    studentId: rawSubmitter.student_id ?? rawSubmitter.studentId ?? rawSubmitter.id,
    userId: rawSubmitter.user_id ?? rawSubmitter.userId,
  } : null
  return {
    id: item.id,
    complaintId: item.id,
    complaintNo: item.complaint_no ?? item.complaintNo,
    category,
    categoryText: COMPLAINT_CATEGORY_TEXT[category] ?? category ?? '--',
    content,
    complaintContent: content,
    status,
    statusText: COMPLAINT_STATUS_TEXT[status] ?? status ?? '--',
    submitter,
    handlingResult,
    handlingResultText: COMPLAINT_HANDLING_RESULT_TEXT[handlingResult] ?? handlingResult ?? '--',
    handlingOpinion: item.handling_opinion ?? item.handlingOpinion ?? '',
    attachments,
    createdAt,
    submittedAt: item.submitted_at ?? item.submittedAt ?? createdAt,
    processingStartedAt: item.processing_started_at ?? item.processingStartedAt ?? null,
    resolvedAt: item.resolved_at ?? item.resolvedAt ?? null,
    updatedAt: item.updated_at ?? item.updatedAt ?? createdAt,

    // Compatibility fields for pages still using the V1 view model.
    contactQq: item.contact_qq ?? item.contactQq,
    submitTime: createdAt,
    complaintMaterials: attachments,
  }
}

export function adaptComplaintEnvelope(payload) {
  if (!payload) return null
  const complaint = payload.complaint ?? payload
  return adaptComplaint({
    ...complaint,
    attachments: payload.attachments ?? complaint.attachments,
    attachment_ids: payload.attachment_ids ?? complaint.attachment_ids,
  })
}

export const adaptComplaintList = (payload) => (
  Array.isArray(payload) ? payload : payload?.items ?? []
).map(adaptComplaint).filter(Boolean)

export const toComplaintPayload = (form) => ({
  category: form.category,
  content: form.complaintContent ?? form.content,
  attachment_ids: form.attachmentIds ?? [],
})
