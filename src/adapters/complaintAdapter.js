import { adaptAttachment } from './taskAdapter.js'

export function adaptComplaint(item) {
  if (!item) return null
  return {
    id: item.id,
    complaintId: item.id,
    complaintNo: item.complaint_no,
    targetType: item.target_type,
    relatedApplicationId: item.target_id,
    complaintContent: item.content,
    isAnonymous: item.is_anonymous,
    status: item.status,
    submitTime: item.created_at,
    complaintMaterials: (item.attachments ?? []).map(adaptAttachment),
  }
}

// complaintType/target 字段是否接受仍待后端确认，当前仅发送契约已声明字段。
export const toComplaintPayload = (form) => ({
  content: form.complaintContent ?? form.content,
  attachment_ids: form.attachmentIds ?? [],
})

