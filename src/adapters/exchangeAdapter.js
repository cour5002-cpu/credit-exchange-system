import { adaptAttachment } from './taskAdapter.js'
import { adaptStudent, adaptTeacher } from './userAdapter.js'

export function adaptExchange(item) {
  if (!item) return null
  return {
    id: item.id,
    exchangeId: item.id,
    exchangeNo: item.exchange_no,
    hourAwardRecordId: item.hour_award_record_id,
    applicationId: item.hour_application_id,
    applicant: adaptStudent(item.applicant),
    leaderStudentId: item.leader_student_id ?? item.hour_award?.leader_student_id,
    teamId: item.team_id ?? item.hour_award?.team_id,
    studentId: item.applicant?.student_no,
    studentName: item.applicant?.name,
    advisor: adaptTeacher(item.advisor),
    finalHours: item.total_hours,
    estimatedCredits: item.estimated_total_credits,
    totalCredit: item.total_credit,
    earnedCredit: item.earned_credit,
    credit: item.credit,
    status: item.status,
    submitTime: item.submitted_at ?? item.created_at,
    updatedAt: item.updated_at,
    hourAward: item.hour_award,
    projectTitle: item.title ?? item.hour_award?.title ?? item.hour_award?.application_title,
    taskName: item.task_title ?? item.hour_award?.task_title ?? item.hour_award?.title,
    teamName: item.team_name ?? item.hour_award?.team_name,
    captainName: item.hour_award?.leader?.name ?? item.applicant?.name,
    advisorConfirmStatus: item.advisor_reviewed_at ? 'approved' : item.status,
    advisorComment: item.advisor_review_comment ?? item.advisor_comment ?? item.reviews?.findLast?.((review) => review.review_role === 'advisor')?.comment,
    advisorConfirmTime: item.advisor_reviewed_at,
    finalComment: item.admin_review_comment ?? item.final_comment,
    finalConfirmTime: item.admin_reviewed_at,
    creditRule: item.conversion_rule ? { ...item.conversion_rule, text: `每 ${item.conversion_rule.hours_per_credit} 课时兑换 1 学分` } : item.rule_snapshot ? { ...item.rule_snapshot, text: `每 ${item.rule_snapshot.hours_per_credit} 课时兑换 1 学分` } : null,
    hoursArrived: true,
    exchanged: item.status === 'final_approved',
    memberDistributions: (item.allocations ?? []).map((row) => ({ student: adaptStudent(row.student), studentDbId: row.student_id ?? row.student?.id, studentId: row.student?.student_no, studentName: row.student?.name, role: row.is_leader ? 'captain' : 'member', allocatedHours: row.hours ?? row.allocated_hours, allocatedCredits: row.allocated_credits, memberHours: row.hours ?? row.allocated_hours, memberCredits: row.allocated_credits, creditType: row.credit_type, remark: row.remark })),
    proofMaterials: (item.attachments ?? []).map(adaptAttachment),
    reviews: item.reviews ?? [],
    actions: item.actions ?? {},
  }
}

export function adaptExchangeEnvelope(payload) {
  if (!payload) return null
  if (!payload.exchange) return adaptExchange(payload)
  return adaptExchange({
    ...payload.exchange,
    allocations: payload.allocations ?? payload.exchange.allocations,
    attachments: payload.attachments ?? payload.exchange.attachments,
    actions: payload.actions ?? payload.exchange.actions,
  })
}

export const adaptExchangeList = (payload) => (
  Array.isArray(payload) ? payload : payload?.items ?? payload?.exchanges ?? []
).map(adaptExchange).filter(Boolean)

export const adaptHourAward = (item) => item && ({
  ...item,
  id: item.id,
  hourAwardRecordId: item.id,
  taskId: item.task_id ?? item.hour_application?.source_task_id,
  leaderStudentId: item.leader_student_id ?? item.leader?.id ?? item.task?.leader_student_id ?? item.hour_application?.leader_student_id ?? item.hour_application?.leader?.id,
  leader: adaptStudent(item.leader ?? item.task?.leader ?? item.hour_application?.leader),
  title: item.title ?? item.application_title ?? item.hour_application?.title,
  status: item.status ?? item.hour_application_status ?? item.hour_application?.status ?? 'final_approved',
  finalHours: Number(item.available_hours ?? item.total_hours ?? item.final_hours ?? 0),
  recognizedHours: Number(item.available_hours ?? item.total_hours ?? item.final_hours ?? 0),
  requestedHours: Number(item.total_hours ?? item.final_hours ?? item.available_hours ?? 0),
  members: item.members ?? [],
  currentStudentRelation: item.current_student_relation ?? null,
})

export const adaptHourAwardList = (payload) => (
  Array.isArray(payload) ? payload : payload?.items ?? []
).map(adaptHourAward).filter(Boolean)

export const toExchangePayload = (form) => ({
  hour_award_record_id: form.hourAwardRecordId,
  allocations: (form.memberDistributions ?? []).map((row) => ({ student_id: Number(row.studentDbId ?? row.student?.id), hours: Number(row.allocatedHours) })),
  attachment_ids: form.attachmentIds ?? [],
  confirm_calculated_credits: true,
})
