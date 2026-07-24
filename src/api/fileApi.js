import { get, post, remove } from './request.js'
import { adaptAttachment } from '../adapters/taskAdapter.js'

export const uploadFile = (file, bizType) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('biz_type', bizType)
  return post('/attachments', formData)
}

export const getAttachment = async (id) => adaptAttachment(await get(`/attachments/${id}`))
export const deleteAttachment = (id) => remove(`/attachments/${id}`)
export const getAttachmentOperationRecords = (id, params) => get(`/admin/attachments/${id}/operation-records`, params)

export async function uploadAttachment(file, bizType) {
  if (!(file instanceof File) && !(file instanceof Blob)) throw new TypeError('file 必须是 File 或 Blob')
  if (!bizType) throw new TypeError('bizType 不能为空')
  const payload = await uploadFile(file, bizType)
  const rawAttachment = payload?.attachment || payload
  if (rawAttachment?.id === undefined || rawAttachment?.id === null) throw new Error('附件上传成功，但响应中缺少 attachment id')
  const attachment = adaptAttachment(rawAttachment)
  return { id: rawAttachment.id, attachment, attachmentIds: [rawAttachment.id] }
}
