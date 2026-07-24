import { adaptAttachment } from './taskAdapter.js'
import { adaptStudent, adaptTeacher } from './userAdapter.js'

const applicationTypeMap = { with_result: 'with_material', without_result: 'without_material', task_result: 'task_result' }
const sourceTypeMap = { self: 'student_self', admin: 'admin_task', advisor: 'teacher_task' }

export function adaptApplication(item) {
  if (!item) return null
  return {
    id: item.id,
    applicationId: item.id,
    applicationNo: item.application_no,
    title: item.title,
    applyType: item.application_type,
    source: item.source_type,
    taskTypeId: item.task_type_id,
    category: item.task_type_name,
    applicant: adaptStudent(item.applicant),
    studentId: item.applicant?.student_no,
    studentName: item.applicant_name ?? item.applicant?.name,
    leader: adaptStudent(item.leader),
    requestedHours: item.requested_hours,
    recognizedHours: item.final_hours,
    reviewerSuggestedHours: item.reviewer_suggested_hours,
    status: item.status,
    submitTime: item.submitted_at,
    createdAt: item.created_at,
    description: item.description,
    expectedResultDate: item.material_due_at,
    members: (item.members ?? []).map((member) => ({ ...adaptStudent(member.student), isLeader: member.is_leader, canView: member.can_view, joinedAt: member.joined_at })),
    advisors: (item.advisors ?? []).map((relation) => ({ teacher: adaptTeacher(relation.teacher), role: relation.advisor_role, canOperate: relation.can_operate, reviewedAt: relation.reviewed_at })),
    attachments: (item.attachments ?? []).map(adaptAttachment),
    reviews: item.reviews ?? [],
    assignments: item.assignments ?? [],
    actions: item.actions ?? {},
  }
}

export const toApplicationPayload = (form) => ({
  title: form.title,
  application_type: applicationTypeMap[form.applyType] ?? form.applicationType ?? form.applyType,
  source_type: sourceTypeMap[form.source] ?? form.sourceType ?? form.source,
  task_type_id: form.taskTypeId,
  requested_hours: Number(form.requestedHours),
  description: form.description || null,
  achievement_summary: form.achievementSummary || null,
  source_task_id: form.taskId || null,
  member_student_ids: (form.members ?? []).map((member) => member.id ?? member.studentId),
  leader_student_id: form.captainId,
  advisor_teacher_ids: [form.mainAdvisor, ...(form.viewAdvisors ?? [])].filter(Boolean).map((teacher) => teacher.id),
  attachment_ids: form.attachmentIds ?? [],
})

