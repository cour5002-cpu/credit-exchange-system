export const STATUS_TEXT = Object.freeze({
  common: {
    draft: '草稿', submitted: '已提交', closed: '已关闭', discarded: '已作废',
    approved: '已通过', rejected: '已驳回', pending: '待处理',
  },
  application: {
    draft: '草稿', submitted: '待指导老师确认', pending_assignment: '待分配审核老师',
    pending_review: '待审核老师审核', pending_admin_final: '待管理员最终确认',
    advisor_rejected: '指导老师已驳回', reviewer_rejected: '审核老师已驳回',
    final_approved: '最终确认通过', final_rejected: '最终确认驳回', appealed: '申诉中',
    pending_material: '待学生补交成果', material_submitted: '补交成果待指导老师确认',
    extension_requested: '普通延期待指导老师确认', extension_admin_review: '特殊延期待管理员审核',
    material_overdue: '成果补交已逾期', closed: '已关闭', discarded: '已作废',
  },
  task: {
    draft: '草稿', pending_publish_review: '待管理员确认发布', publish_rejected: '发布被驳回',
    published: '已发布', registration_open: '报名中', registration_closed: '报名已截止',
    selection_pending: '待筛选成员', leader_pending: '待指定队长', task_in_progress: '任务进行中',
    result_submitted: '成果已提交', result_approved: '成果已通过', closed: '已关闭', discarded: '已作废',
  },
  taskResult: { submitted: '待指导老师确认', advisor_rejected: '指导老师已驳回', converted_to_hour_application: '已转入课时认定' },
  registration: { submitted: '已报名', selected: '已选中', not_selected: '未选中', canceled: '已取消' },
  exchange: {
    draft: '草稿', submitted: '待指导老师确认', advisor_approved: '指导老师已通过',
    advisor_rejected: '指导老师已驳回', pending_admin_final: '待管理员最终确认',
    final_approved: '最终确认通过', final_rejected: '最终确认驳回', appealed: '申诉中',
    closed: '已关闭', discarded: '已作废',
  },
  appeal: {
    pending_admin_review: '待管理员处理', processing: '处理中', completed: '已完成',
  },
  complaint: {
    submitted: '已提交', viewed: '管理员已查看',
    // TODO: V1 契约不包含 processed；需确认是否保留“已处理”状态与处理意见。
  },
  extension: {
    submitted: '已提交', approved: '已通过', rejected: '已驳回', closed: '已关闭',
  },
})

export function getStatusText(status, scope = 'common') {
  return STATUS_TEXT[scope]?.[status] ?? STATUS_TEXT.common[status] ?? status ?? '--'
}
