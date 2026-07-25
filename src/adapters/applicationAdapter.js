import { adaptAttachment } from './taskAdapter.js'
import { adaptStudent, adaptTeacher } from './userAdapter.js'

const applicationTypeMap = { with_result: 'with_material', without_result: 'without_material', task_result: 'task_result' }

export function adaptApplication(item) {
  if (!item) return null
  const advisorRelation = (item.advisors ?? []).find((relation) => relation.advisor_role === 'primary')
  const viewAdvisorRelations = (item.advisors ?? []).filter((relation) => relation.advisor_role !== 'primary')
  const reviewerReview = [...(item.reviews ?? [])].reverse().find((review) => String(review.review_result ?? review.result ?? '').includes('reviewer'))
  const advisorReview = [...(item.reviews ?? [])].reverse().find((review) => String(review.review_result ?? review.result ?? '').includes('advisor'))
  const finalReview = [...(item.reviews ?? [])].reverse().find((review) => String(review.review_result ?? review.result ?? '').includes('final'))
  const reviewerResult = item.reviewer_result ?? reviewerReview
  const sourceTextMap = { student_self: '学生自主申请', admin_task: '管理员任务', teacher_task: '指导老师任务' }
  const typeTextMap = { with_material: '有成果申请', without_material: '无成果申请', task_result: '任务成果申请' }
  return {
    id: item.id,
    applicationId: item.id,
    applicationNo: item.application_no,
    title: item.title,
    applyType: item.application_type,
    applyTypeText: typeTextMap[item.application_type] ?? item.application_type,
    source: item.source_type,
    sourceText: sourceTextMap[item.source_type] ?? item.source_type ?? '课时申请',
    taskTypeId: item.task_type_id,
    category: item.task_type_name,
    applicant: adaptStudent(item.applicant),
    studentId: item.applicant?.student_no,
    studentName: item.applicant_name ?? item.applicant?.name,
    leader: adaptStudent(item.leader),
    requestedHours: item.requested_hours,
    recognizedHours: item.final_hours,
    originalHours: item.requested_hours,
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
    canOperate: item.can_operate ?? item.can_review ?? advisorRelation?.can_operate ?? false,
    mainAdvisor: adaptTeacher(advisorRelation?.teacher ?? item.advisor),
    viewAdvisors: viewAdvisorRelations.map((relation) => adaptTeacher(relation.teacher)).filter(Boolean),
    advisorStatus: advisorReview ? 'approved' : '',
    advisorComment: advisorReview?.comment ?? '',
    advisorConfirmTime: advisorReview?.created_at ?? advisorReview?.reviewed_at ?? '',
    adminAcceptComment: item.assignments?.at(-1)?.comment ?? '',
    adminAcceptTime: item.assignments?.at(-1)?.created_at ?? '',
    reviewer: adaptTeacher(reviewerResult?.reviewer ?? reviewerResult?.teacher),
    reviewStatus: reviewerResult?.review_result ?? reviewerResult?.result ?? '',
    reviewComment: reviewerResult?.comment ?? '',
    reviewTime: reviewerResult?.created_at ?? reviewerResult?.reviewed_at ?? '',
    finalStatus: item.status === 'final_approved' ? 'approved' : item.status === 'final_rejected' ? 'rejected' : '',
    finalComment: finalReview?.comment ?? '',
    finalConfirmTime: finalReview?.created_at ?? finalReview?.reviewed_at ?? '',
    canReview: item.can_review ?? item.actions?.can_review,
  }
}

export function adaptApplicationEnvelope(payload) {
  if (!payload) return null
  if (!payload.application) return adaptApplication(payload)
  return adaptApplication({
    ...payload.application,
    applicant: payload.applicant ?? payload.application.applicant,
    members: payload.members ?? payload.application.members,
    advisors: payload.advisors ?? payload.application.advisors,
    attachments: payload.attachments ?? payload.application.attachments,
    reviews: payload.reviews ?? payload.application.reviews,
    assignments: payload.assignments ?? payload.application.assignments,
    reviewer_result: payload.reviewer_result ?? payload.application.reviewer_result,
    final_hours: payload.final_hours ?? payload.application.final_hours,
    requested_hours: payload.requested_hours ?? payload.application.requested_hours,
    can_review: payload.can_review ?? payload.application.can_review,
    can_operate: payload.can_operate ?? payload.application.can_operate,
    actions: payload.actions ?? payload.application.actions,
  })
}

export const adaptApplicationList = (payload) => ({
  ...(payload ?? {}),
  items: (Array.isArray(payload) ? payload : payload?.items ?? []).map(adaptApplication),
})

export const toApplicationPayload = (form) => ({
  title: form.title,
  application_type: applicationTypeMap[form.applyType] ?? form.applicationType ?? form.applyType,
  task_type_id: form.taskTypeId,
  requested_hours: Number(form.requestedHours),
  description: form.description || null,
  advisor_teacher_id: Number(form.advisorTeacherId ?? form.mainAdvisor?.id ?? form.mainAdvisor),
  view_teacher_ids: (form.viewTeacherIds ?? form.viewAdvisors ?? []).map((teacher) => Number(teacher.id ?? teacher)),
  attachment_ids: form.attachmentIds ?? [],
})
