import { adaptAttachment } from './taskAdapter.js'
import { adaptStudent, adaptTeacher } from './userAdapter.js'
import { adaptExtensionRule } from './extensionRuleAdapter.js'

const applicationTypeMap = { with_result: 'with_material', without_result: 'without_material', task_result: 'task_result' }

const attachmentList = (value) => Array.isArray(value) ? value : []
const attachmentRefs = (value) => attachmentList(value).map((attachment) => (
  typeof attachment === 'object' && attachment !== null ? attachment : { id: attachment }
))
const uniqueAttachments = (...groups) => [...new Map(
  groups.flatMap(attachmentRefs).filter((attachment) => attachment.id !== undefined && attachment.id !== null)
    .map((attachment) => [String(attachment.id), attachment])
).values()]

export function adaptApplication(item) {
  if (!item) return null
  const taskResultSubmission = item.task_result_submission ?? null
  const materialSubmission = item.material_submission ?? item.latest_material_submission ?? item.supplement_submission ?? item.material_submissions?.at(-1) ?? null
  const sourceTask = item.source_task ?? taskResultSubmission?.task ?? null
  const team = item.team ?? taskResultSubmission?.team ?? sourceTask?.team ?? null
  const rawMembers = item.members ?? team?.members ?? taskResultSubmission?.members ?? sourceTask?.members ?? []
  const members = rawMembers.map((relation) => {
    const rawStudent = relation.student ?? relation
    const student = adaptStudent({ ...rawStudent, student_no: rawStudent.student_no ?? rawStudent.studentNo })
    const isLeader = relation.is_leader ?? ['leader', 'captain'].includes(relation.role ?? relation.member_role)
    return student && {
      ...student,
      isLeader: Boolean(isLeader),
      role: isLeader ? 'captain' : 'member',
      canView: relation.can_view,
      joinedAt: relation.joined_at,
    }
  }).filter(Boolean)
  const leader = adaptStudent(team?.leader ?? item.leader ?? rawMembers.find((relation) => relation.is_leader)?.student)
  const attachments = uniqueAttachments(item.attachments, item.material_attachments, item.attachment_ids, item.material_attachment_ids, item.result_attachment_ids, materialSubmission?.attachments, materialSubmission?.attachment_ids, materialSubmission?.material_attachment_ids, taskResultSubmission?.attachments, taskResultSubmission?.attachment_ids)
  const advisorRelation = (item.advisors ?? []).find((relation) => relation.advisor_role === 'primary')
  const viewAdvisorRelations = (item.advisors ?? []).filter((relation) => relation.advisor_role !== 'primary')
  const reviewerReview = [...(item.reviews ?? [])].reverse().find((review) => (
    review.stage === 'reviewer'
    || review.operator_role === 'reviewer'
  ))
  const advisorReview = [...(item.reviews ?? [])].reverse().find((review) => (
    review.stage === 'advisor'
    || review.operator_role === 'advisor'
  ))
  const finalReview = [...(item.reviews ?? [])].reverse().find((review) => (
    ['admin_final', 'final'].includes(review.stage)
    || (
      review.operator_role === 'admin'
      && ['final_approved', 'final_rejected'].includes(review.after_status)
    )
  ))
  const reviewerResult = item.reviewer_result ?? reviewerReview
  const reviewerDecision = reviewerResult?.decision ?? reviewerResult?.review_result ?? reviewerResult?.result ?? ''
  const reviewerStatus = reviewerDecision === 'rejected'
    ? 'rejected'
    : reviewerDecision === 'approved'
      ? 'approved'
      : reviewerDecision === 'modified_approved'
        ? 'modified_approved'
        : ''
  const adminDecision = finalReview?.decision ?? ''
  const adminStatus = adminDecision === 'rejected'
    ? 'rejected'
    : adminDecision === 'approved'
      ? 'approved'
      : ''
  const sourceTextMap = { student_self: '学生自主申请', admin_task: '管理员任务', teacher_task: '指导老师任务' }
  const typeTextMap = { with_material: '有成果申请', without_material: '无成果申请', task_result: '任务成果申请' }
  return {
    id: item.id,
    applicationId: item.id,
    applicationNo: item.application_no,
    title: item.title,
    applyType: item.application_type,
    applicationType: item.application_type,
    applyTypeText: typeTextMap[item.application_type] ?? item.application_type,
    source: item.source_type ?? item.source,
    sourceText: sourceTextMap[item.source_type ?? item.source] ?? item.source_type ?? item.source ?? '课时申请',
    taskTypeId: item.task_type_id,
    category: item.task_type_name,
    taskId: item.source_task_id ?? sourceTask?.id ?? taskResultSubmission?.task_id,
    taskTitle: item.task_title ?? sourceTask?.title ?? taskResultSubmission?.task_title,
    team: team ? {
      id: team.id,
      name: team.name ?? team.team_name ?? sourceTask?.team_name,
      leader,
      members,
    } : (members.length ? { id: item.team_id, name: item.team_name, leader, members } : null),
    teamId: item.team_id ?? team?.id ?? taskResultSubmission?.team_id ?? sourceTask?.team_id,
    teamName: item.team_name ?? team?.name ?? team?.team_name ?? sourceTask?.team_name,
    leader,
    captainId: leader?.id,
    applicant: adaptStudent(item.applicant),
    studentId: item.applicant?.student_no,
    studentName: item.applicant_name ?? item.applicant?.name,
    leader: adaptStudent(item.leader),
    requestedHours: item.requested_hours,
    recognizedHours: item.final_hours,
    originalHours: item.requested_hours,
    reviewerSuggestedHours: item.reviewer_suggested_hours,
    status: item.status,
    advisorTeacherId: item.advisor_teacher_id ?? advisorRelation?.teacher?.id ?? item.advisor?.id,
    submitTime: item.submitted_at,
    createdAt: item.created_at,
    description: item.description,
    expectedResultDate: item.material_due_at,
    extensionCount: Number(item.extension_count ?? 0),
    extensionApplied: Number(item.extension_count ?? 0) > 0 || Boolean(item.extension_request ?? item.extension_applied),
    extensionStatus: item.extension_status ?? (item.status === 'extension_requested' ? 'pending_advisor' : item.status === 'extension_admin_review' ? 'pending_admin' : Number(item.extension_count ?? 0) > 0 ? 'approved' : ''),
    resultDescription: item.achievement_summary ?? item.result_summary ?? taskResultSubmission?.summary ?? taskResultSubmission?.achievement_summary ?? item.description ?? '',
    resultMaterials: attachments.map(adaptAttachment),
    proofMaterials: [],
    supplementTime: item.material_submitted_at ?? item.updated_at,
    members,
    advisors: (item.advisors ?? []).map((relation) => ({ teacher: adaptTeacher(relation.teacher), role: relation.advisor_role, canOperate: relation.can_operate, reviewedAt: relation.reviewed_at })),
    attachments: attachments.map(adaptAttachment),
    reviews: item.reviews ?? [],
    assignments: item.assignments ?? [],
    actions: item.actions ?? {},
    canOperate: item.can_operate ?? item.can_review ?? advisorRelation?.can_operate ?? false,
    mainAdvisor: adaptTeacher(advisorRelation?.teacher ?? item.advisor),
    viewAdvisors: viewAdvisorRelations.map((relation) => adaptTeacher(relation.teacher)).filter(Boolean),
    advisorStatus: advisorReview?.decision === 'rejected'
      ? 'rejected'
      : advisorReview?.decision === 'approved'
        ? 'approved'
        : '',
    advisorComment: advisorReview?.comment ?? '',
    advisorConfirmTime: advisorReview?.created_at ?? advisorReview?.reviewed_at ?? '',
    adminAcceptComment: item.assignments?.at(-1)?.comment ?? '',
    adminAcceptTime: item.assignments?.at(-1)?.created_at ?? '',
    reviewer: adaptTeacher(reviewerResult?.reviewer ?? reviewerResult?.teacher),
    reviewerStatus,
    reviewerComment: reviewerResult?.comment ?? '',
    reviewStatus: reviewerStatus,
    reviewComment: reviewerResult?.comment ?? '',
    reviewTime: reviewerResult?.created_at ?? reviewerResult?.reviewed_at ?? '',
    adminStatus: adminStatus || (item.status === 'final_approved' ? 'approved' : item.status === 'final_rejected' ? 'rejected' : ''),
    adminComment: finalReview?.comment ?? '',
    finalStatus: adminStatus || (item.status === 'final_approved' ? 'approved' : item.status === 'final_rejected' ? 'rejected' : ''),
    finalComment: finalReview?.comment ?? '',
    finalConfirmTime: finalReview?.created_at ?? finalReview?.reviewed_at ?? '',
    canReview: item.can_review ?? item.actions?.can_review,
  }
}

export function adaptApplicationEnvelope(payload) {
  if (!payload) return null
  if (!payload.application) return adaptApplication(payload)
  const taskResultSubmission = payload.task_result_submission ?? payload.application.task_result_submission
  const materialSubmission = payload.material_submission ?? payload.latest_material_submission ?? payload.supplement_submission ?? payload.material_submissions?.at(-1) ?? payload.application.material_submission ?? payload.application.latest_material_submission ?? payload.application.supplement_submission ?? payload.application.material_submissions?.at(-1)
  const attachments = uniqueAttachments(payload.attachments, payload.attachment_ids, payload.material_attachment_ids, payload.result_attachment_ids, payload.application.attachments, payload.application.attachment_ids, payload.application.material_attachments, payload.application.material_attachment_ids, payload.application.result_attachment_ids, materialSubmission?.attachments, materialSubmission?.attachment_ids, materialSubmission?.material_attachment_ids, taskResultSubmission?.attachments, taskResultSubmission?.attachment_ids)
  return adaptApplication({
    ...payload.application,
    applicant: payload.applicant ?? payload.application.applicant,
    members: payload.members ?? payload.application.members,
    advisors: payload.advisors ?? payload.application.advisors,
    attachments,
    task_result_submission: taskResultSubmission,
    source_task: payload.source_task ?? payload.task ?? payload.application.source_task,
    team: payload.team ?? payload.application.team,
    team_id: payload.team_id ?? payload.application.team_id,
    team_name: payload.team_name ?? payload.application.team_name,
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
  items: (Array.isArray(payload) ? payload : payload?.items ?? payload?.applications ?? payload?.records ?? []).map(adaptApplication),
})

export function adaptExtensionEligibility(data) {
  if (!data) return null
  const source = data.eligibility ?? data
  return {
    canApply: Boolean(source.can_apply),
    reasonCode: source.reason_code,
    reason: source.reason,
    currentDueAt: source.current_due_at,
    submittedRequestCount: Number(source.submitted_request_count ?? 0),
    approvedExtensionDays: Number(source.approved_extension_days ?? 0),
    remainingRequestCount: Number(source.remaining_request_count ?? 0),
    remainingExtensionDays: Number(source.remaining_extension_days ?? 0),
    expectedGraduationDate: source.expected_graduation_date,
    rule: source.rule ? adaptExtensionRule(source.rule) : null,
  }
}

export function adaptExtensionRequest(payload) {
  if (!payload) return null
  const extension = payload.extension_request ?? payload
  const application = adaptApplication(payload.application ?? extension.application)
  const applicant = adaptStudent(extension.applicant ?? extension.student)
  const extensionAttachments = uniqueAttachments(payload.attachments, payload.attachment_ids, payload.proof_attachment_ids, extension.attachments, extension.attachment_ids, extension.proof_attachment_ids, payload.attachment ? [payload.attachment] : [], extension.attachment ? [extension.attachment] : [], extension.attachment_id ? [{ id: extension.attachment_id, file_name: extension.filename }] : [])
  const reviewLevel = extension.review_level === 'advisor' ? 'normal' : extension.review_level === 'admin' ? 'special' : extension.review_level
  const status = extension.status === 'submitted'
    ? (reviewLevel === 'special' ? 'pending_admin_review' : 'pending_advisor_review')
    : extension.status
  const rawRuleSnapshot = extension.rule_snapshot ?? payload.rule_snapshot ?? null
  const ruleSnapshot = rawRuleSnapshot ? {
    ...rawRuleSnapshot,
    ...adaptExtensionRule(rawRuleSnapshot),
  } : null
  return {
    id: extension.id ?? extension.extension_request_id,
    applicationId: extension.application_id ?? extension.hour_application_id ?? application?.id,
    applicant,
    studentName: extension.applicant_name ?? applicant?.name ?? application?.studentName,
    studentId: applicant?.studentNo ?? application?.studentId,
    oldDueAt: extension.old_due_at,
    requestedDueAt: extension.requested_due_at,
    extensionDays: extension.extension_days,
    reason: extension.reason,
    reviewLevel,
    status,
    reviewComment: extension.review_comment,
    createdAt: extension.created_at,
    reviewedAt: extension.reviewed_at,
    actions: payload.actions ?? extension.actions ?? {},
    canOperate: payload.can_operate ?? extension.can_operate ?? false,
    application,
    title: application?.title,
    applyTypeText: application?.applyTypeText,
    requestedHours: application?.requestedHours,
    mainAdvisor: application?.mainAdvisor,
    originalExpectedResultTime: extension.old_due_at,
    newExpectedResultTime: extension.requested_due_at,
    extensionReason: extension.reason,
    extensionSubmitTime: extension.created_at,
    extensionMaterials: extensionAttachments.map(adaptAttachment),
    ruleSnapshot,
    rawRuleSnapshot,
  }
}

export const adaptExtensionList = (payload) => ({
  ...(payload ?? {}),
  items: (Array.isArray(payload) ? payload : payload?.items ?? []).map(adaptExtensionRequest),
})

export function toApplicationPayload(form) {
  const members = form.members ?? []
  const memberStudentIds = members.map((member) => Number(member.studentDbId))
  const leader = members.find((member) => member.isLeader)
  return {
    title: form.title,
    application_type: applicationTypeMap[form.applyType] ?? form.applicationType ?? form.applyType,
    task_type_id: form.taskTypeId,
    requested_hours: Number(form.requestedHours),
    description: form.description || null,
    advisor_teacher_id: Number(form.advisorTeacherId ?? form.mainAdvisor?.id ?? form.mainAdvisor),
    view_teacher_ids: (form.viewTeacherIds ?? form.viewAdvisors ?? []).map((teacher) => Number(teacher.id ?? teacher)),
    attachment_ids: form.attachmentIds ?? [],
    member_count: members.length,
    member_student_ids: memberStudentIds,
    leader_student_id: Number(leader?.studentDbId),
    ...(form.expectedResultDate ? { material_due_at: form.expectedResultDate } : {}),
  }
}
