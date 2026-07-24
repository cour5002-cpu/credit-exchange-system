import { adaptStudent, adaptTeacher } from './userAdapter.js'

export function adaptAttachment(item) {
  if (!item) return null
  return { id: item.id, name: item.file_name, size: item.file_size, type: item.mime_type, url: item.url, uploadedAt: item.created_at, bizType: item.biz_type }
}

export function adaptTask(task) {
  if (!task) return null
  return {
    id: task.id,
    taskId: task.id,
    taskNo: task.task_no,
    title: task.title,
    publisherRole: task.publisher_role,
    publisherName: task.publisher_name,
    taskTypeId: task.task_type_id,
    taskType: task.task_type_name,
    description: task.description,
    resultRequirement: task.result_requirement ?? task.requirement,
    registrationDeadline: task.registration_deadline,
    resultDeadline: task.material_due_at,
    status: task.status,
    createdAt: task.created_at,
    advisor: adaptTeacher(task.advisor),
    registrations: (task.registrations ?? []).map((item) => ({ ...item, student: adaptStudent(item.student), studentId: item.student?.student_no, studentName: item.student?.name, applyStatus: item.status, applyTime: item.submitted_at })),
    members: (task.members ?? []).map((item) => ({ ...item, student: adaptStudent(item.student), studentId: item.student?.student_no, studentName: item.student?.name, isLeader: item.is_leader })),
    leader: adaptStudent(task.leader),
    resultSubmission: adaptTaskResult(task.result_submission),
    actions: task.actions ?? {},
  }
}

export function adaptTaskResult(result) {
  if (!result) return null
  return { id: result.id, resultId: result.id, taskId: result.task_id, leader: adaptStudent(result.leader), leaderId: result.leader?.student_no, leaderName: result.leader?.name, resultDescription: result.summary ?? result.achievement_summary, requestedHours: result.requested_hours, resultMaterials: (result.attachments ?? []).map(adaptAttachment), versions: result.versions ?? [], status: result.status, submitTime: result.submitted_at }
}

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
  registration_deadline: task.registrationDeadline,
  advisor_teacher_id: task.advisorId,
  attachment_ids: task.attachmentIds ?? [],
})
