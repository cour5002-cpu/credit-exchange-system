import { adaptAttachment } from './taskAdapter.js'

export function adaptComplaint(item) {
  if (!item) return null
  const attachments = (
    item.attachments ?? (item.attachment_ids ?? []).map((id) => ({ id }))
  ).map(adaptAttachment).filter(Boolean)
  return {
    id: item.id,
    complaintId: item.id,
    complaintNo: item.complaint_no,
    complaintContent: item.content,
    contactQq: item.contact_qq,
    status: item.status,
    submitTime: item.created_at,
    attachments,
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
  content: form.complaintContent ?? form.content,
  contact_qq: form.contactQq ?? form.contact_qq,
  attachment_ids: form.attachmentIds ?? [],
})
