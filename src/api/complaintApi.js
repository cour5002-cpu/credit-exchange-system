import { get, post } from './request.js'

export const submitStudentComplaint = (data) => post('/student/complaints', data)
export const getStudentComplaints = (params) => get('/student/complaints', params)
export const getStudentComplaint = (id) => get(`/student/complaints/${id}`)
export const getAdminComplaints = (params) => get('/admin/complaints', params)
export const getAdminComplaint = (id) => get(`/admin/complaints/${id}`)
export const startProcessingComplaint = (id) => post(`/admin/complaints/${id}/start-processing`)
export const resolveComplaint = (id, data) => post(`/admin/complaints/${id}/resolve`, data)

// Keep the existing public name for pages that have not migrated yet.
export const submitComplaint = submitStudentComplaint
