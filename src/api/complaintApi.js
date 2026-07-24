import { get, post } from './request.js'

export const submitComplaint = (data) => post('/student/complaints', data)
export const getAdminComplaints = (params) => get('/admin/complaints', params)
export const getAdminComplaint = (id) => get(`/admin/complaints/${id}`)

