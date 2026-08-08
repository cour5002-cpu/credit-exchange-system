import { get, post } from './request.js'

export const getRuleFiles = (params) => get('/rule-files', params)

export const createRuleFile = (data) => post('/admin/rule-files', data)

function getDownloadFileName(disposition, fallback) {
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  if (encoded) return decodeURIComponent(encoded)
  return disposition.match(/filename="?([^";]+)"?/i)?.[1] || fallback
}

export async function getRuleFileBlob(id) {
  const response = await fetch(`/api/v1/rule-files/${id}/download`, {
    method: 'GET',
    credentials: 'include',
  })
  const contentType = response.headers.get('content-type') || ''
  if (!response.ok || contentType.toLowerCase().includes('application/json')) {
    const error = new Error('规则文件下载失败')
    error.status = response.status
    throw error
  }
  return {
    blob: await response.blob(),
    disposition: response.headers.get('content-disposition') || '',
  }
}

export async function downloadRuleFile(id, fallbackName = '规则文件') {
  const { blob, disposition } = await getRuleFileBlob(id)
  const blobUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = getDownloadFileName(disposition, fallbackName)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 0)
}
