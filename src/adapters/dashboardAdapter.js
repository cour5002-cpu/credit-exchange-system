const adaptDashboardItem = (item) => {
  if (!item) return null
  const { biz_id, biz_no, submitted_by, created_at, ...rest } = item
  return {
    ...rest,
    bizId: biz_id,
    bizNo: biz_no,
    submittedBy: submitted_by,
    createdAt: created_at,
  }
}

const adaptDashboardSection = (section) => {
  if (!section) return null
  const { todo_type, list_api, items, ...rest } = section
  return {
    ...rest,
    label: todo_type === 'complaint_unviewed' ? '未完成投诉' : rest.label,
    todoType: todo_type,
    listApi: list_api,
    items: (Array.isArray(items) ? items : []).map(adaptDashboardItem).filter(Boolean),
  }
}

export function adaptAdminDashboard(data) {
  if (!data) return null
  const {
    total_pending,
    refresh_interval_seconds,
    generated_at,
    sections,
    ...rest
  } = data
  return {
    ...rest,
    totalPending: total_pending,
    refreshIntervalSeconds: refresh_interval_seconds,
    generatedAt: generated_at,
    sections: (Array.isArray(sections) ? sections : [])
      .map(adaptDashboardSection)
      .filter(Boolean),
  }
}
