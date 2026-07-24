export function adaptRecord(item) {
  if (!item) return null
  return {
    id: item.id,
    targetType: item.target_type,
    targetId: item.target_id,
    operatorRole: item.operator_role,
    operatorName: item.operator_name,
    action: item.action,
    beforeStatus: item.before_status,
    afterStatus: item.after_status,
    comment: item.comment,
    createdAt: item.created_at,
  }
}

