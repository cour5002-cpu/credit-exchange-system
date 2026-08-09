import { get } from './request.js'

export const getAdminDashboard = () => {
  return get('/admin/dashboard')
}
