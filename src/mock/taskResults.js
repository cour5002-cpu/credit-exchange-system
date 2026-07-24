import { addApplication, getApplications } from './applications.js'

export const TASK_RESULT_STATUS = Object.freeze({
  SUBMITTED: 'submitted',
  ADVISOR_REJECTED: 'advisor_rejected',
  CONVERTED_TO_HOUR_APPLICATION: 'converted_to_hour_application',
  PENDING_ADVISOR_RESULT_CONFIRM: 'submitted',
  ADVISOR_RESULT_APPROVED: 'converted_to_hour_application',
  ADVISOR_RESULT_REJECTED: 'advisor_rejected',
  APPLICATION_CREATED: 'converted_to_hour_application',
})

const taskResults = []

function nowText() {
  const date = new Date(); const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function getTaskResults() { return taskResults }
export function getTaskResult(resultId) { return taskResults.find((result) => result.resultId === resultId) }
export function getTaskResultById(resultId) { return getTaskResult(resultId) }
export function getTaskResultByTaskId(taskId) { return [...taskResults].reverse().find((result) => result.taskId === taskId) }
export function hasActiveTaskResult(taskId) {
  const activeStatuses = [TASK_RESULT_STATUS.SUBMITTED, TASK_RESULT_STATUS.CONVERTED_TO_HOUR_APPLICATION]
  return taskResults.some((result) => result.taskId === taskId && activeStatuses.includes(result.status))
}
export function hasTaskResult(taskId) { return hasActiveTaskResult(taskId) }

export function addTaskResult(data) {
  if (!data?.taskId || hasActiveTaskResult(data.taskId)) return null
  const result = {
    resultId: data.resultId || `RESULT-${Date.now()}`,
    taskId: '', taskTitle: '', taskHours: 0, leaderId: '', leaderName: '', advisorId: '', advisorName: '',
    teamMembers: [], resultDescription: '', resultMaterials: [], proofMaterials: [], submitTime: nowText(),
    status: TASK_RESULT_STATUS.SUBMITTED, advisorComment: '', advisorConfirmTime: '', applicationId: '', versions: [],
    ...data,
    status: TASK_RESULT_STATUS.SUBMITTED,
  }
  result.versions.push({ versionNo: 1, summary: result.resultDescription, requestedHours: result.requestedHours, attachments: [...result.resultMaterials, ...result.proofMaterials].map((file) => ({ ...file })), submittedAt: result.submitTime })
  taskResults.push(result)
  const linkedApplication = addApplication({
    title: `${result.taskTitle}课时申请`, studentName: result.leaderName, studentId: result.leaderId,
    source: 'task_result', applyType: 'task_result', requestedHours: result.requestedHours,
    taskId: result.taskId, taskTitle: result.taskTitle, resultId: result.resultId,
    leaderId: result.leaderId, leaderName: result.leaderName, members: result.teamMembers,
    mainAdvisor: { id: result.advisorId, name: result.advisorName },
    attachments: [...result.resultMaterials, ...result.proofMaterials],
  })
  linkedApplication.status = 'material_submitted'
  result.applicationId = linkedApplication.id
  return result
}

export function getPendingAdvisorTaskResults(advisorId = '') {
  return taskResults.filter((result) => result.status === TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM && (!advisorId || result.advisorId === advisorId))
}
export function getAdvisorPendingTaskResults(advisorId = '') { return getPendingAdvisorTaskResults(advisorId) }

export function advisorApproveTaskResult(resultId, comment = '') {
  const result = getTaskResult(resultId)
  if (!result || result.status !== TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM) return null
  result.status = TASK_RESULT_STATUS.CONVERTED_TO_HOUR_APPLICATION
  const application = getApplications().find((item) => item.id === result.applicationId)
  if (application) application.status = 'pending_assignment'
  result.advisorComment = comment.trim()
  result.advisorConfirmTime = nowText()
  return result
}
export function approveTaskResult(resultId, comment = '') { return advisorApproveTaskResult(resultId, comment) }

export function advisorRejectTaskResult(resultId, comment) {
  const result = getTaskResult(resultId)
  if (!result || result.status !== TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM || !comment?.trim()) return null
  result.status = TASK_RESULT_STATUS.ADVISOR_REJECTED
  const application = getApplications().find((item) => item.id === result.applicationId)
  if (application) application.status = 'material_submitted'
  result.advisorComment = comment.trim()
  result.advisorConfirmTime = nowText()
  return result
}
export function rejectTaskResult(resultId, comment) { return advisorRejectTaskResult(resultId, comment) }

export function getApprovedTaskResultsForStudent(studentId) {
  return taskResults.filter((result) => result.status === TASK_RESULT_STATUS.ADVISOR_RESULT_APPROVED && (result.leaderId === studentId || result.teamMembers.some((member) => member.studentId === studentId)))
}

export function markTaskResultApplicationCreated(resultId, applicationId = '') {
  const result = getTaskResult(resultId)
  if (!result || result.status !== TASK_RESULT_STATUS.ADVISOR_RESULT_APPROVED) return null
  result.status = TASK_RESULT_STATUS.APPLICATION_CREATED
  result.applicationId = applicationId
  return result
}

export function resubmitTaskResult(resultId, data) {
  const result = getTaskResult(resultId)
  if (!result || result.status !== TASK_RESULT_STATUS.ADVISOR_REJECTED) return null
  if (!data?.resultDescription?.trim() || Number(data.requestedHours) <= 0 || !data.resultMaterials?.length) return null
  result.resultDescription = data.resultDescription.trim()
  result.requestedHours = Number(data.requestedHours)
  result.taskHours = Number(data.requestedHours)
  result.resultMaterials = data.resultMaterials.map((file) => ({ ...file }))
  result.proofMaterials = (data.proofMaterials || []).map((file) => ({ ...file }))
  result.submitTime = nowText()
  result.advisorComment = ''
  result.advisorConfirmTime = ''
  result.status = TASK_RESULT_STATUS.SUBMITTED
  const application = getApplications().find((item) => item.id === result.applicationId)
  if (application) {
    application.requestedHours = result.requestedHours
    application.resultDescription = result.resultDescription
    application.resultMaterials = result.resultMaterials.map((file) => ({ ...file }))
    application.proofMaterials = result.proofMaterials.map((file) => ({ ...file }))
    application.attachments = [...application.resultMaterials, ...application.proofMaterials]
    application.status = 'material_submitted'
  }
  result.versions.push({ versionNo: result.versions.length + 1, summary: result.resultDescription, requestedHours: result.requestedHours, attachments: [...result.resultMaterials, ...result.proofMaterials].map((file) => ({ ...file })), submittedAt: result.submitTime })
  return result
}
