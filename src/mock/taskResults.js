export const TASK_RESULT_STATUS = Object.freeze({
  PENDING_ADVISOR_RESULT_CONFIRM: 'pending_advisor_result_confirm',
  ADVISOR_RESULT_APPROVED: 'advisor_result_approved',
  ADVISOR_RESULT_REJECTED: 'advisor_result_rejected',
  APPLICATION_CREATED: 'application_created',
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
  const activeStatuses = [TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM, TASK_RESULT_STATUS.ADVISOR_RESULT_APPROVED, TASK_RESULT_STATUS.APPLICATION_CREATED]
  return taskResults.some((result) => result.taskId === taskId && activeStatuses.includes(result.status))
}
export function hasTaskResult(taskId) { return hasActiveTaskResult(taskId) }

export function addTaskResult(data) {
  if (!data?.taskId || hasActiveTaskResult(data.taskId)) return null
  const result = {
    resultId: data.resultId || `RESULT-${Date.now()}`,
    taskId: '', taskTitle: '', taskHours: 0, leaderId: '', leaderName: '', advisorId: '', advisorName: '',
    teamMembers: [], resultDescription: '', resultMaterials: [], proofMaterials: [], submitTime: nowText(),
    status: TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM, advisorComment: '', advisorConfirmTime: '', applicationId: '',
    ...data,
    status: TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM,
  }
  taskResults.push(result)
  return result
}

export function getPendingAdvisorTaskResults(advisorId = '') {
  return taskResults.filter((result) => result.status === TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM && (!advisorId || result.advisorId === advisorId))
}
export function getAdvisorPendingTaskResults(advisorId = '') { return getPendingAdvisorTaskResults(advisorId) }

export function advisorApproveTaskResult(resultId, comment = '') {
  const result = getTaskResult(resultId)
  if (!result || result.status !== TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM) return null
  result.status = TASK_RESULT_STATUS.ADVISOR_RESULT_APPROVED
  result.advisorComment = comment.trim()
  result.advisorConfirmTime = nowText()
  return result
}
export function approveTaskResult(resultId, comment = '') { return advisorApproveTaskResult(resultId, comment) }

export function advisorRejectTaskResult(resultId, comment) {
  const result = getTaskResult(resultId)
  if (!result || result.status !== TASK_RESULT_STATUS.PENDING_ADVISOR_RESULT_CONFIRM || !comment?.trim()) return null
  result.status = TASK_RESULT_STATUS.ADVISOR_RESULT_REJECTED
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
