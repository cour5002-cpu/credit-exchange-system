import { adaptStudent, adaptTeacher } from './userAdapter.js'
import { toShanghaiIso } from '../utils/taskDateTime.js'

export function adaptAttachment(item) {
  if (!item) return null
  return { id: item.id, name: item.file_name ?? item.filename ?? item.name ?? item.fileName, size: item.file_size ?? item.size ?? item.fileSize, type: item.mime_type ?? item.type ?? item.fileType, url: item.url, uploadedAt: item.created_at ?? item.uploaded_at ?? item.uploadedAt ?? item.uploadTime, bizType: item.biz_type ?? item.bizType }
}

const taskAttachments = (task) => {
  const attachments = task.attachments ?? task.task_attachments ?? (task.attachment_ids ?? []).map((id) => ({ id }))
  return attachments.map(adaptAttachment).filter(Boolean)
}

export function adaptTask(task) {
  if (!task) return null
  const taskType = task.task_type ?? null
  const advisor = task.advisor ?? task.advisor_teacher ?? null
  const registrations = adaptTaskRegistrations(task.registrations)
  const members = (task.members ?? []).map((item) => ({ ...item, student: adaptStudent(item.student), studentId: item.student?.student_no, studentName: item.student?.name, isLeader: item.is_leader }))
  return {
    id: task.id,
    taskId: task.id,
    taskNo: task.task_no,
    title: task.title,
    publisherRole: task.publisher_role,
    source: task.source ?? task.publisher_role,
    publisherName: task.publisher_name,
    taskTypeId: task.task_type_id ?? taskType?.id,
    taskType: task.task_type_name ?? taskType?.name,
    taskTypeName: task.task_type_name ?? taskType?.name,
    description: task.description,
    requirement: task.requirement ?? task.result_requirement,
    resultRequirement: task.result_requirement ?? task.requirement,
    category: task.category ?? task.project_category,
    hours: task.hours ?? task.requested_hours,
    registrationStartTime: task.registration_start_time ?? task.registration_started_at,
    registrationDeadline: task.registration_deadline,
    resultDeadline: task.material_due_at,
    maxParticipants: task.max_participants,
    status: task.status ?? task.task_status,
    createdAt: task.created_at,
    submitTime: task.submitted_at ?? task.created_at,
    publishTime: task.published_at,
    advisor: adaptTeacher(advisor),
    advisorId: task.advisor_teacher_id ?? advisor?.id,
    advisorName: advisor?.name ?? task.advisor_teacher_name ?? task.publisher_name,
    attachments: taskAttachments(task),
    registrations,
    applicants: registrations,
    members,
    selectedStudents: members.length ? members : registrations.filter((item) => item.selected),
    leader: adaptStudent(task.leader),
    leaderId: task.leader?.id,
    leaderName: task.leader?.name,
    resultSubmission: adaptTaskResult(task.result_submission),
    actions: task.actions ?? {},
    myRegistration: adaptTaskRegistration(task.my_registration),
    hourApplications: task.hour_applications ?? task.applications ?? [],
    canRegister: task.actions?.can_register ?? task.can_register ?? false,
  }
}

export function adaptTaskRegistration(item) {
  if (!item) return null
  const student = adaptStudent(item.student)
  return {
    ...item,
    id: item.id,
    registrationId: item.id,
    student,
    studentDbId: item.student?.id,
    studentId: item.student?.student_no,
    studentName: item.student?.name,
    college: student?.college || item.student?.college_name || '',
    major: student?.major || item.student?.major_name || '',
    className: student?.className || item.student?.class_name || '',
    applyStatus: item.status,
    applyTime: item.registered_at ?? item.submitted_at,
    selected: item.status === 'selected',
  }
}

export const adaptTaskRegistrations = (payload) => (
  Array.isArray(payload) ? payload : payload?.items ?? payload?.registrations ?? []
).map(adaptTaskRegistration).filter(Boolean)

const attachmentItems = (...groups) => [...new Map(
  groups.flatMap((group) => Array.isArray(group) ? group : [])
    .map((attachment) => typeof attachment === 'object' && attachment !== null ? attachment : { id: attachment })
    .filter((attachment) => attachment.id !== undefined && attachment.id !== null)
    .map((attachment) => [String(attachment.id), attachment])
).values()]

export function adaptTaskResult(result) {
  if (!result) return null
  const submission = result.submission ?? result.task_result_submission ?? result
  const task = adaptTask(result.task ?? submission.task)
  const attachments = attachmentItems(
    result.attachment_ids,
    result.submission?.attachment_ids,
    result.task_result_submission?.attachment_ids,
    submission.attachment_ids,
    result.attachments,
    result.submission?.attachments,
    result.task_result_submission?.attachments,
    submission.attachments,
  ).map(adaptAttachment).filter(Boolean)
  return { id: submission.id, resultId: submission.id, taskId: submission.task_id ?? task?.id, task, taskTitle: submission.task_title ?? task?.title, advisorName: submission.advisor_name ?? task?.advisorName, leader: adaptStudent(submission.leader), leaderId: submission.leader?.id, leaderName: submission.leader?.name, teamMembers: (result.members ?? submission.members ?? []).map((item) => ({ ...adaptStudent(item.student ?? item), role: item.is_leader ? 'captain' : 'member' })), resultDescription: submission.summary ?? submission.achievement_summary, requestedHours: submission.requested_hours, attachments, resultMaterials: attachments, proofMaterials: [], actions: result.actions ?? submission.actions ?? {}, canOperate: result.can_operate ?? submission.can_operate ?? false, versions: submission.versions ?? [], status: submission.status, submitTime: submission.submitted_at }
}

export const adaptTaskEnvelope = (payload) => adaptTask(payload?.task ? { ...payload.task, attachments: payload.attachments ?? payload.task.attachments, attachment_ids: payload.attachment_ids ?? payload.task.attachment_ids, my_registration: payload.my_registration ?? payload.task.my_registration, actions: payload.actions ?? payload.task.actions, can_register: payload.can_register ?? payload.task.can_register, registrations: payload.registrations ?? payload.items ?? payload.task.registrations, members: payload.members ?? payload.task.members, leader: payload.leader ?? payload.task.leader, result_submission: payload.result_submission ?? payload.task.result_submission } : payload)
export const adaptTaskList = (payload) => (Array.isArray(payload) ? payload : payload?.items ?? payload?.tasks ?? []).map(adaptTask)
export const adaptTaskResultEnvelope = (payload) => {
  if (!payload) return null
  const submission = payload.result_submission ?? payload.submission ?? payload.task_result_submission ?? payload
  return adaptTaskResult({
    ...submission,
    submission,
    task: payload.task ?? submission.task,
    attachments: payload.attachments ?? submission.attachments,
    attachment_ids: payload.attachment_ids ?? submission.attachment_ids,
    members: payload.members ?? submission.members,
  })
}
export const adaptTaskResultList = (payload) => (Array.isArray(payload) ? payload : payload?.items ?? payload?.submissions ?? []).map(adaptTaskResult)

export const toTaskResultPayload = (form) => ({
  summary: form.summary ?? form.description,
  requested_hours: Number(form.requestedHours),
  attachment_ids: form.attachmentIds ?? [],
})

export const toTaskPayload = (task) => ({
  title: task.title,
  task_type_id: task.taskTypeId ?? task.task_type_id,
  description: task.description,
  result_requirement: task.resultRequirement ?? task.result_requirement,
  registration_deadline: toShanghaiIso(task.registrationDeadline),
  advisor_teacher_id: task.advisorId,
  attachment_ids: task.attachmentIds ?? [],
})

export const toAdvisorTaskPayload = (task) => ({
  title: task.title,
  description: task.description,
  task_type_id: Number(task.taskTypeId),
  result_requirement: task.resultRequirement,
  registration_deadline: toShanghaiIso(task.registrationDeadline),
  attachment_ids: task.attachmentIds ?? [],
})
