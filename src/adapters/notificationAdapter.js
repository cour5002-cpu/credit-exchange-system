export function adaptNotification(item) {
  if (!item) return null
  return {
    id: item.id,
    notificationId: item.id,
    title: item.title,
    content: item.content,
    relatedBizType: item.target_type,
    relatedBizId: item.target_id,
    isRead: item.is_read,
    createTime: item.created_at,
  }
}

