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

function getAttachmentFileUrl(attachment) {
  return `/api/v1/attachments/${attachment.id}?download=true`
}

async function getAttachmentBlob(attachment) {
  const response = await fetch(getAttachmentFileUrl(attachment), {
    method: 'GET',
    credentials: 'include',
  })
  const contentType = response.headers.get('content-type') || ''
  if (!response.ok || contentType.toLowerCase().includes('application/json')) {
    const error = new Error('附件下载失败')
    error.status = response.status
    throw error
  }
  return response.blob()
}

export function getAttachmentErrorMessage(error, action = 'preview') {
  const status = Number(error?.status ?? error?.response?.status)
  const code = Number(error?.code)
  if (status === 403 || code === 40301) {
    return action === 'download' ? '您没有权限下载该文件' : '您没有权限查看该附件'
  }
  if (status === 404 || code === 40401) return '附件不存在'
  return '附件加载失败'
}

function getPreviewType(attachment) {
  const mimeType = String(attachment.type || '').toLowerCase()
  const fileName = String(attachment.name || '').toLowerCase()
  if (mimeType.startsWith('image/') || /\.(png|jpe?g|gif|webp|bmp|svg)$/.test(fileName)) return 'image'
  if (mimeType === 'application/pdf' || fileName.endsWith('.pdf')) return 'pdf'
  if (/word|officedocument\.wordprocessingml/.test(mimeType) || /\.docx?$/.test(fileName)) return 'document'
  if (/excel|spreadsheetml/.test(mimeType) || /\.xlsx?$/.test(fileName)) return 'spreadsheet'
  return 'file'
}

function createAttachmentDialog(attachment, previewUrl = '') {
  const previewType = getPreviewType(attachment)
  const overlay = document.createElement('div')
  const dialog = document.createElement('section')
  const header = document.createElement('header')
  const titleGroup = document.createElement('div')
  const title = document.createElement('strong')
  const meta = document.createElement('small')
  const closeButton = document.createElement('button')
  const content = document.createElement('div')
  const actions = document.createElement('footer')
  const downloadButton = document.createElement('button')

  overlay.style.cssText = 'position:fixed;inset:0;z-index:10000;display:grid;place-items:center;padding:24px;background:rgba(15,23,42,.72)'
  dialog.style.cssText = 'display:flex;flex-direction:column;width:min(100%,1000px);height:min(88vh,800px);overflow:hidden;border-radius:14px;background:#fff;box-shadow:0 24px 60px rgba(15,23,42,.35)'
  header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 20px;border-bottom:1px solid #e2e8f0'
  titleGroup.style.cssText = 'min-width:0'
  title.style.cssText = 'display:block;overflow:hidden;color:#1e293b;text-overflow:ellipsis;white-space:nowrap'
  meta.style.cssText = 'display:block;margin-top:4px;color:#64748b'
  closeButton.style.cssText = 'padding:7px 12px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;cursor:pointer'
  content.style.cssText = 'display:grid;min-height:0;flex:1;place-items:center;overflow:auto;padding:18px;background:#f8fafc'
  actions.style.cssText = 'display:flex;justify-content:flex-end;padding:12px 20px;border-top:1px solid #e2e8f0'
  downloadButton.style.cssText = 'padding:9px 16px;border:0;border-radius:8px;color:#fff;background:#2563eb;font-weight:700;cursor:pointer'

  title.textContent = attachment.name || `附件 ${attachment.id}`
  meta.textContent = attachment.type || '未知文件类型'
  closeButton.type = 'button'
  closeButton.textContent = '关闭'
  downloadButton.type = 'button'
  downloadButton.textContent = '下载附件'

  if (previewType === 'image') {
    const image = document.createElement('img')
    image.src = previewUrl
    image.alt = attachment.name || '附件图片'
    image.style.cssText = 'display:block;max-width:100%;max-height:100%;object-fit:contain'
    content.appendChild(image)
  } else if (previewType === 'pdf') {
    const frame = document.createElement('iframe')
    frame.src = previewUrl
    frame.title = attachment.name || 'PDF 附件预览'
    frame.style.cssText = 'width:100%;height:100%;min-height:520px;border:0;background:#fff'
    content.style.padding = '0'
    content.appendChild(frame)
  } else {
    const information = document.createElement('div')
    const kind = previewType === 'document' ? 'Word 文档' : previewType === 'spreadsheet' ? 'Excel 工作簿' : '该类型文件'
    information.style.cssText = 'max-width:520px;padding:28px;text-align:center;color:#475569'
    information.textContent = `${kind}不支持在线预览，请下载后查看。`
    content.appendChild(information)
  }

  const close = () => {
    document.removeEventListener('keydown', onKeydown)
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    overlay.remove()
  }
  const onKeydown = (event) => { if (event.key === 'Escape') close() }
  closeButton.addEventListener('click', close)
  overlay.addEventListener('click', (event) => { if (event.target === overlay) close() })
  downloadButton.addEventListener('click', async () => {
    try { await downloadAttachment(attachment) } catch (error) { window.alert(getAttachmentErrorMessage(error, 'download')) }
  })
  document.addEventListener('keydown', onKeydown)

  titleGroup.append(title, meta)
  header.append(titleGroup, closeButton)
  actions.appendChild(downloadButton)
  dialog.append(header, content, actions)
  overlay.appendChild(dialog)
  document.body.appendChild(overlay)
}

export async function previewAttachment(file) {
  const attachment = await getAttachment(file?.id ?? file)
  const previewType = getPreviewType(attachment)
  const previewUrl = ['image', 'pdf'].includes(previewType)
    ? URL.createObjectURL(await getAttachmentBlob(attachment))
    : ''
  createAttachmentDialog(attachment, previewUrl)
  return attachment
}

export async function downloadAttachment(file) {
  const attachment = await getAttachment(file?.id ?? file)
  const blob = await getAttachmentBlob(attachment)
  const blobUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = attachment.name || ''
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 0)
  return attachment
}

export async function uploadAttachment(file, bizType) {
  if (!(file instanceof File) && !(file instanceof Blob)) throw new TypeError('file 必须是 File 或 Blob')
  if (!bizType) throw new TypeError('bizType 不能为空')
  const payload = await uploadFile(file, bizType)
  const rawAttachment = payload?.attachment || payload
  if (rawAttachment?.id === undefined || rawAttachment?.id === null) throw new Error('附件上传成功，但响应中缺少 attachment id')
  const attachment = adaptAttachment(rawAttachment)
  return { id: rawAttachment.id, attachment, attachmentIds: [rawAttachment.id] }
}
