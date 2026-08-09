export function adaptNotification(item) {
  if (!item) return null
  return {
    id: item.id,
    title: item.title,
    content: item.content,
    category: item.category,
    messageType: item.message_type,
    bizType: item.biz_type,
    bizId: item.biz_id,
    bizAvailable: item.biz_available,
    isRead: item.is_read,
    readAt: item.read_at,
    createdAt: item.created_at,
  }
}
