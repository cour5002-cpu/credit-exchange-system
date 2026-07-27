import { adaptStudent, adaptTeacher } from './userAdapter.js'
import { toShanghaiIso } from '../utils/taskDateTime.js'

export function adaptAttachment(item) {
  if (!item) return null
  return { id: item.id, name: item.file_name, size: item.file_size, type: item.mime_type, url: item.url, uploadedAt: item.created_at, bizType: item.biz_type }
}

export function adaptTask(task) {
  if (!task) return null
  const taskType = task.task_type ?? null
  const advisor = task.advisor ?? task.advisor_teacher ?? null
  return {
    id: task.id,
    taskId: task.id,
    taskNo: task.task_no,
    title: task.title,
    publisherRole: task.publisher_role,
    publisherName: task.publisher_name,
    taskTypeId: task.task_type_id ?? taskType?.id,
    taskType: task.task_type_name ?? taskType?.name,
    taskTypeName: task.task_type_name ?? taskType?.name,
    description: task.description,
    resultRequirement: task.result_requirement ?? task.requirement,
    registrationDeadline: task.registration_deadline,
    resultDeadline: task.material_due_at,
    status: task.status ?? task.task_status,
    createdAt: task.created_at,
    submitTime: task.submitted_at ?? task.created_at,
    publishTime: task.published_at,
    advisor: adaptTeacher(advisor),
    advisorId: task.advisor_teacher_id ?? advisor?.id,
    advisorName: advisor?.name ?? task.advisor_teacher_name ?? task.publisher_name,
    attachments: (task.attachments ?? []).map(adaptAttachment),
    registrations: adaptTaskRegistrations(task.registrations),
    applicants: adaptTaskRegistrations(task.registrations),
    members: (task.members ?? []).map((item) => ({ ...item, student: adaptStudent(item.student), studentId: item.student?.student_no, studentName: item.student?.name, isLeader: item.is_leader })),
    leader: adaptStudent(task.leader),
    leaderId: task.leader?.id,
    leaderName: task.leader?.name,
    resultSubmission: adaptTaskResult(task.result_submission),
    actions: task.actions ?? {},
    myRegistration: task.my_registration ?? null,
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

export function adaptTaskResult(result) {
  if (!result) return null
  const task = adaptTask(result.task)
  return { id: result.id, resultId: result.id, taskId: result.task_id ?? task?.id, task, taskTitle: result.task_title ?? task?.title, advisorName: result.advisor_name ?? task?.advisorName, leader: adaptStudent(result.leader), leaderId: result.leader?.id, leaderName: result.leader?.name, teamMembers: (result.members ?? []).map((item) => ({ ...adaptStudent(item.student ?? item), role: item.is_leader ? 'captain' : 'member' })), resultDescription: result.summary ?? result.achievement_summary, requestedHours: result.requested_hours, resultMaterials: (result.attachments ?? []).map(adaptAttachment), proofMaterials: [], actions: result.actions ?? {}, canOperate: result.can_operate ?? false, versions: result.versions ?? [], status: result.status, submitTime: result.submitted_at }
}

export const adaptTaskEnvelope = (payload) => adaptTask(payload?.task ? { ...payload.task, my_registration: payload.my_registration ?? payload.task.my_registration, actions: payload.actions ?? payload.task.actions, can_register: payload.can_register ?? payload.task.can_register, registrations: payload.registrations ?? payload.items ?? payload.task.registrations, members: payload.members ?? payload.task.members, leader: payload.leader ?? payload.task.leader, result_submission: payload.result_submission ?? payload.task.result_submission } : payload)
export const adaptTaskList = (payload) => (Array.isArray(payload) ? payload : payload?.items ?? payload?.tasks ?? []).map(adaptTask)
export const adaptTaskResultEnvelope = (payload) => {
  if (!payload) return null
  const submission = payload.result_submission ?? payload.submission ?? payload
  return adaptTaskResult({
    ...submission,
    task: payload.task ?? submission.task,
    attachments: payload.attachments ?? submission.attachments,
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
})
