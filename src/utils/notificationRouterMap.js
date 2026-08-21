const notificationRouteMap = Object.freeze({
  hour_application: Object.freeze({
    student: (id) => `/student/hour-progress/${id}`,
    advisor: (id) => `/teacher/confirm/${id}`,
    admin: (id) => `/admin/final-confirm/${id}`,
  }),
  credit_exchange: Object.freeze({
    student: (id) => `/student/credit-exchange-records/${id}`,
    advisor: (id) => `/teacher/confirm/exchanges/${id}`,
    admin: (id) => `/admin/final-confirm/exchanges/${id}`,
  }),
  extension_request: Object.freeze({
    advisor: (id) => `/teacher/confirm/extensions/${id}`,
  }),
  college_task: Object.freeze({
    student: (id) => `/student/tasks/${id}`,
    advisor: (id) => `/teacher/publish-task/${id}`,
  }),
  appeal: Object.freeze({
    student: (id) => `/student/appeals/${id}`,
    admin: (id) => `/admin/appeals-complaints/${id}`,
    reviewer: (id) => `/reviewer/appeal-reviews/${id}`,
  }),
  complaint: Object.freeze({
    student: (id) => `/student/complaints/${id}`,
    admin: (id) => `/admin/appeals-complaints/complaints/${id}`,
  }),
})

export function getNotificationBizPath(notification, role) {
  if (!notification || notification.bizAvailable === false || notification.biz_available === false) return null
  const bizType = notification.bizType ?? notification.biz_type
  const bizId = notification.bizId ?? notification.biz_id
  const createPath = notificationRouteMap[bizType]?.[role]
  const missingBizId = bizId === undefined || bizId === null || bizId === ''
  if (!createPath || missingBizId) return null
  return createPath(encodeURIComponent(String(bizId ?? '')))
}

export { notificationRouteMap }
