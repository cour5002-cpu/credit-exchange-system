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
    studentId: item.applicant?.student_no,
    studentName: item.applicant?.name,
    advisor: adaptTeacher(item.advisor),
    finalHours: item.total_hours,
    estimatedCredits: item.estimated_total_credits,
    status: item.status,
    submitTime: item.submitted_at,
    hourAward: item.hour_award,
    memberDistributions: (item.allocations ?? []).map((row) => ({ student: adaptStudent(row.student), studentId: row.student?.student_no, studentName: row.student?.name, allocatedHours: row.allocated_hours, allocatedCredits: row.allocated_credits, creditType: row.credit_type, remark: row.remark })),
    proofMaterials: (item.attachments ?? []).map(adaptAttachment),
    reviews: item.reviews ?? [],
    actions: item.actions ?? {},
  }
}

export const toExchangePayload = (form) => ({
  hour_award_record_id: form.hourAwardRecordId,
  allocations: (form.memberDistributions ?? []).map((row) => ({ student_id: row.studentId ?? row.student?.id, allocated_hours: Number(row.allocatedHours), allocated_credits: Number(row.allocatedCredits), credit_type: row.creditType, remark: row.remark || null })),
  attachment_ids: form.attachmentIds ?? [],
})

