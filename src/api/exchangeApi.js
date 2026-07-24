import { get, post } from './request.js'

export const getAvailableHourAwards = (params) => get('/student/credit-exchanges/available-hour-awards', params)
export const getExchangeFormData = (params) => get('/student/credit-exchanges/form-data', params)
export const saveExchangeDraft = (data) => post('/student/credit-exchanges/drafts', data)
export const submitExchange = (data) => post('/student/credit-exchanges', data)
export const getStudentExchanges = (params) => get('/student/credit-exchanges', params)
export const getStudentExchange = (id) => get(`/student/credit-exchanges/${id}`)
export const getAdvisorPendingExchanges = (params) => get('/advisor/credit-exchanges/pending', params)
export const getAdvisorExchange = (id) => get(`/advisor/credit-exchanges/${id}`)
export const approveExchangeByAdvisor = (id, data = {}) => post(`/advisor/credit-exchanges/${id}/approve`, data)
export const rejectExchangeByAdvisor = (id, data) => post(`/advisor/credit-exchanges/${id}/reject`, data)
export const getAdminPendingExchanges = (params) => get('/admin/credit-exchanges/pending-final', params)
export const getAdminExchange = (id) => get(`/admin/credit-exchanges/${id}`)
export const finalApproveExchange = (id, data = {}) => post(`/admin/credit-exchanges/${id}/final-approve`, data)
export const finalRejectExchange = (id, data) => post(`/admin/credit-exchanges/${id}/final-reject`, data)
export const batchApproveExchanges = (data) => post('/admin/credit-exchanges/batch-approve', data)
export const getCurrentConversionRule = () => get('/credit-conversion-rules/current')

