export function adaptRecord(item) {
  if (!item) return null
  const target = item.target ?? {}
  const details = item.details ?? item.detail ?? item.metadata ?? {}
  return {
    id: item.id,
    targetType: item.target_type ?? item.biz_type,
    targetId: item.target_id ?? target.id,
    operatorRole: item.operator_role,
    operatorName: item.operator_name,
    action: item.action,
    beforeStatus: item.before_status,
    afterStatus: item.after_status,
    comment: item.comment,
    createdAt: item.created_at,
    type: item.biz_type_name ?? item.action_name ?? item.action ?? item.target_type ?? item.biz_type ?? '--',
    title: item.target_title ?? target.title ?? target.name ?? target.application_title ?? target.task_title ?? `${item.target_type ?? item.biz_type ?? '业务'} #${item.target_id ?? target.id ?? '--'}`,
    person: item.target_person_name ?? target.student_name ?? target.applicant_name ?? target.leader_name ?? item.operator_name ?? '--',
    result: item.result ?? item.decision ?? item.after_status ?? '--',
    status: item.current_status ?? target.status ?? item.after_status ?? '',
    currentStatus: item.current_status ?? target.status ?? item.after_status ?? '',
    time: item.created_at,
    sourceId: item.target_id ?? target.id,
    detail: details,
    target,
  }
}

export const adaptRecordList = (payload) => (
  Array.isArray(payload) ? payload : payload?.items ?? payload?.records ?? []
).map(adaptRecord).filter(Boolean)

export function adaptRecordEnvelope(payload) {
  if (!payload) return null
  if (!payload.record) return adaptRecord(payload)
  return adaptRecord({ ...payload.record, target: payload.target ?? payload.record.target })
}
