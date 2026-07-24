export const BASE_URL = '/api/v1'

export const requestConfig = Object.freeze({
  baseURL: BASE_URL,
  withCredentials: true,
})

export const API_ERROR_CODES = Object.freeze({
  UNAUTHORIZED: 40101,
  FORBIDDEN: 40301,
  CONFLICT: 40901,
})

export class ApiError extends Error {
  constructor(message, options = {}) {
    super(message || '请求失败')
    this.name = 'ApiError'
    this.code = options.code ?? null
    this.status = options.status ?? null
    this.data = options.data ?? null
    this.category = options.category || 'business'
    this.response = options.response ?? null
  }
}

function getErrorCategory(code, status) {
  if (code === API_ERROR_CODES.UNAUTHORIZED || status === 401) return 'unauthorized'
  if (code === API_ERROR_CODES.FORBIDDEN || status === 403) return 'forbidden'
  if (code === API_ERROR_CODES.CONFLICT || status === 409) return 'conflict'
  if (status >= 500) return 'server'
  if (status >= 400) return 'http'
  return 'business'
}

function createUrl(path, params) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = normalizedPath.startsWith(`${BASE_URL}/`) || normalizedPath === BASE_URL
    ? normalizedPath
    : `${BASE_URL}${normalizedPath}`
  if (!params) return url
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    if (Array.isArray(value)) value.forEach((item) => search.append(key, item))
    else search.append(key, value)
  })
  const query = search.toString()
  return query ? `${url}?${query}` : url
}

async function parseResponse(response) {
  if (response.status === 204) return { code: 0, message: 'success', data: null }
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    const message = await response.text()
    throw new ApiError(message || `HTTP ${response.status}`, {
      status: response.status,
      category: getErrorCategory(null, response.status),
      response,
    })
  }
  return response.json()
}

export async function request(path, options = {}) {
  const { params, body, headers, ...fetchOptions } = options
  const requestHeaders = new Headers(headers || {})
  let requestBody = body

  if (body !== undefined && body !== null && !(body instanceof FormData) && !(body instanceof Blob) && typeof body !== 'string') {
    requestHeaders.set('Content-Type', 'application/json')
    requestBody = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(createUrl(path, params), {
      ...fetchOptions,
      method: fetchOptions.method || 'GET',
      headers: requestHeaders,
      body: requestBody,
      credentials: 'include',
    })
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(error?.message || '网络连接失败', { category: 'network' })
  }

  const payload = await parseResponse(response)
  const code = Number(payload?.code)
  if (!response.ok || code !== 0) {
    throw new ApiError(payload?.message || `HTTP ${response.status}`, {
      code: Number.isFinite(code) ? code : null,
      status: response.status,
      data: payload?.data ?? null,
      category: getErrorCategory(code, response.status),
      response,
    })
  }
  return payload.data
}

export const get = (path, params, options = {}) => request(path, { ...options, method: 'GET', params })
export const post = (path, body, options = {}) => request(path, { ...options, method: 'POST', body })
export const put = (path, body, options = {}) => request(path, { ...options, method: 'PUT', body })
export const patch = (path, body, options = {}) => request(path, { ...options, method: 'PATCH', body })
export const remove = (path, options = {}) => request(path, { ...options, method: 'DELETE' })

