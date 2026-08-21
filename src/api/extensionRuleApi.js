import { get, patch, post } from './request.js'

export const createExtensionRule = (data) => post('/admin/extension-rules', data)
export const getExtensionRules = (params) => get('/admin/extension-rules', params)
export const getExtensionRule = (id) => get(`/admin/extension-rules/${id}`)
export const getCurrentExtensionRule = (params) => get('/extension-rules/current', params)
export const updateExtensionRule = (id, data) => patch(`/admin/extension-rules/${id}`, data)
export const enableExtensionRule = (id, data) => post(`/admin/extension-rules/${id}/enable`, data)
export const disableExtensionRule = (id, data) => post(`/admin/extension-rules/${id}/disable`, data)
