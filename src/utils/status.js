const STATUS_META = {
  pending: { text: '待处理', color: 'warning' },
  pending_review: { text: '待审核', color: 'warning' },
  reviewing: { text: '审核中', color: 'info' },
  pending_confirmation: { text: '待确认', color: 'warning' },
  confirmed: { text: '已确认', color: 'success' },
  pending_acceptance: { text: '待受理', color: 'warning' },
  accepted: { text: '已受理', color: 'success' },
  pending_final_confirmation: { text: '待最终确认', color: 'warning' },
  final_approved: { text: '最终通过', color: 'success' },
  final_rejected: { text: '最终驳回', color: 'danger' },
  approved: { text: '已通过', color: 'success' },
  rejected: { text: '已驳回', color: 'danger' },
  completed: { text: '已完成', color: 'success' },
  cancelled: { text: '已取消', color: 'default' },
  enabled: { text: '已启用', color: 'success' },
  disabled: { text: '已停用', color: 'default' },
}

const STAGE_DESCRIPTIONS = {
  submitted: '申请已提交，等待处理。',
  advisor_review: '等待指导老师审核。',
  reviewer_review: '等待审核老师审核。',
  admin_review: '等待管理员审核。',
  final_confirmation: '审核已完成，等待最终确认。',
  completed: '流程已完成。',
  rejected: '申请未通过，请查看审核意见。',
  cancelled: '流程已取消。',
}

function normalizeValue(value) {
  return typeof value === 'string' ? value.trim().toLowerCase() : ''
}

export function getStatusText(status) {
  if (status === null || status === undefined || status === '') return '未知状态'
  return STATUS_META[normalizeValue(status)]?.text ?? String(status)
}

export function getStatusColor(status) {
  return STATUS_META[normalizeValue(status)]?.color ?? 'default'
}

export function getStageDescription(stage) {
  if (stage === null || stage === undefined || stage === '') return '暂无阶段信息。'
  return STAGE_DESCRIPTIONS[normalizeValue(stage)] ?? String(stage)
}
