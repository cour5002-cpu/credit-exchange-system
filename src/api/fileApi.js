import { get, post, remove } from './request.js'

export const uploadFile = (file, bizType) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('biz_type', bizType)
  return post('/attachments', formData)
}

export const getAttachment = (id) => get(`/attachments/${id}`)
export const deleteAttachment = (id) => remove(`/attachments/${id}`)
export const getAttachmentOperationRecords = (id, params) => get(`/admin/attachments/${id}/operation-records`, params)

export async function uploadAttachment(file, bizType) {
  if (!(file instanceof File) && !(file instanceof Blob)) throw new TypeError('file 必须是 File 或 Blob')
  if (!bizType) throw new TypeError('bizType 不能为空')
  const payload = await uploadFile(file, bizType)
  const attachment = payload?.attachment || payload
  if (attachment?.id === undefined || attachment?.id === null) throw new Error('附件上传成功，但响应中缺少 attachment id')
  return { id: attachment.id, attachment }
}

