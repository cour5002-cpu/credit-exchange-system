import { get } from './request.js'

// 后端暂未实现通知接口。以下方法仅预留契约入口，现有页面继续使用 Mock。
export const getNotifications = (params) => get('/notifications', params)
export const getNotification = (id) => get(`/notifications/${id}`)

// TODO: 后端契约尚未定义单条已读和全部已读接口。
