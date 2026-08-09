import { get, post } from './request.js'

export const getNotifications = (params) => get('/notifications', params)
export const getNotificationDetail = (id) => get(`/notifications/${id}`)
export const getUnreadCount = () => get('/notifications/unread-count')
export const markNotificationRead = (id) => post(`/notifications/${id}/read`)
export const markAllNotificationsRead = () => post('/notifications/read-all')
