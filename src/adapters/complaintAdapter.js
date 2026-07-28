import { adaptAttachment } from './taskAdapter.js'

export function adaptComplaint(item) {
  if (!item) return null
  return {
    id: item.id,
    complaintId: item.id,
    complaintNo: item.complaint_no,
    complaintContent: item.content,
    status: item.status,
    submitTime: item.created_at,
    complaintMaterials: (item.attachments ?? []).map(adaptAttachment),
  }
}

export function adaptComplaintEnvelope(payload) {
  if (!payload) return null
  const complaint = payload.complaint ?? payload
  return adaptComplaint({ ...complaint, attachments: payload.attachments ?? complaint.attachments })
}

export const adaptComplaintList = (payload) => (
  Array.isArray(payload) ? payload : payload?.items ?? []
).map(adaptComplaint).filter(Boolean)

export const toComplaintPayload = (form) => ({
  content: form.complaintContent ?? form.content,
  attachment_ids: form.attachmentIds ?? [],
})
