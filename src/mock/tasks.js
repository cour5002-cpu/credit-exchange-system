export const TASK_STATUS = Object.freeze({
  DRAFT: 'draft',
  PENDING_ADMIN_PUBLISH: 'pending_admin_publish',
  PUBLISHED: 'published',
  PUBLISH_REJECTED: 'publish_rejected',
  CLOSED: 'closed',
  SELECTING: 'selecting',
  SELECTED: 'selected',
  LEADER_ASSIGNED: 'leader_assigned',
  IN_PROGRESS: 'in_progress',
  RESULT_SUBMITTED: 'result_submitted',
  FINISHED: 'finished',
})

export const TASK_TYPE_OPTIONS = Object.freeze([
  { value: 'volunteer_service', label: '志愿服务' },
  { value: 'innovation', label: '创新创业' },
  { value: 'social_practice', label: '社会实践' },
  { value: 'competition', label: '学科竞赛' },
  { value: 'campus_service', label: '校园服务' },
])

export const ADMIN_TASK_ADVISORS = Object.freeze([
  { advisorId: 'T001', advisorName: '张明', college: '计算机学院' },
  { advisorId: 'T002', advisorName: '李华', college: '管理学院' },
  { advisorId: 'T003', advisorName: '王芳', college: '艺术学院' },
])

const tasks = [
  {
    taskId: 'TASK-2026-001', title: '校园数字化志愿服务', taskType: 'volunteer_service', hours: 16,
    description: '协助整理校园活动数字档案，并完成现场志愿服务。', requirement: '责任心强，能够按时参加线下活动。',
    resultRequirement: '提交服务记录、活动照片及不少于 800 字的总结。', advisorId: 'T001', advisorName: '张明', source: 'advisor',
    registrationDeadline: '2026-08-20 18:00', attachments: [{ id: 'TASK-ATT-001', name: '任务安排说明.pdf', type: 'PDF', size: '1.2 MB', uploadedAt: '2026-07-20 10:15' }],
    status: TASK_STATUS.PENDING_ADMIN_PUBLISH, submitTime: '2026-07-20 10:20', publishTime: '', adminComment: '', adminConfirmTime: '',
    applicants: [], selectedStudents: [], leaderId: '', leaderName: '',
  },
  {
    taskId: 'TASK-2026-002', title: '创新项目调研助手', taskType: 'innovation', hours: 20,
    description: '参与创新创业项目的用户访谈和竞品资料整理。', requirement: '具备基础调研与文档整理能力。',
    resultRequirement: '提交调研纪要、竞品分析表及个人工作总结。', advisorId: 'T001', advisorName: '张明', source: 'advisor',
    registrationDeadline: '2026-08-25 18:00', attachments: [], status: TASK_STATUS.PUBLISH_REJECTED,
    submitTime: '2026-07-18 14:30', publishTime: '', adminComment: '报名条件描述过于宽泛，请补充具体能力要求。', adminConfirmTime: '2026-07-19 09:15',
    applicants: [], selectedStudents: [], leaderId: '', leaderName: '',
  },
  {
    taskId: 'TASK-2026-003', title: '社区科普活动策划', taskType: 'social_practice', hours: 24,
    description: '面向社区青少年策划并实施一次信息安全科普活动。', requirement: '可组队报名，有宣讲或活动策划经验者优先。',
    resultRequirement: '提交策划书、现场记录、参与反馈和成果总结。', advisorId: 'T001', advisorName: '张明', source: 'advisor',
    registrationDeadline: '2026-08-15 18:00', attachments: [], status: TASK_STATUS.PUBLISHED,
    submitTime: '2026-07-10 11:00', publishTime: '2026-07-11 09:00', adminComment: '确认发布。', adminConfirmTime: '2026-07-11 09:00',
    applicants: [], selectedStudents: [], leaderId: '', leaderName: '',
  },
]

function nowText() {
  const date = new Date(); const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function normalizeTask(task) {
  const taskId = task.taskId || `TASK-${Date.now()}`
  const normalized = { taskId, title: '', taskType: '', hours: 0, description: '', requirement: '', resultRequirement: '', category: '', advisorId: '', advisorName: '', source: 'advisor', publishSource: '', publisherRole: '', publisherName: '', registrationStartTime: '', registrationDeadline: '', resultDeadline: '', maxParticipants: 0, attachments: [], status: TASK_STATUS.DRAFT, submitTime: '', publishTime: '', adminComment: '', adminConfirmTime: '', applicants: [], selectedStudents: [], leaderId: '', leaderName: '', selectionTime: '', leaderAssignTime: '', ...task, taskId }
  normalized.attachments = (task.attachments || []).map((file, index) => ({
    id: file.id || `TASK-ATT-${Date.now()}-${index}`,
    name: file.name || file.fileName || '',
    type: file.type || file.fileType || '未知类型',
    size: file.size || file.fileSize || '--',
    uploadedAt: file.uploadedAt || file.uploadTime || nowText(),
    mockUrl: file.mockUrl || '',
  }))
  return normalized
}

export function getTasks() { return tasks }
export function getTask(taskId) { return tasks.find((task) => task.taskId === taskId) }
export function getTaskById(taskId) { return getTask(taskId) }
export function getAdvisorTasks(advisorId) { return tasks.filter((task) => task.advisorId === advisorId && task.source === 'advisor') }
export function getPendingAdminPublishTasks() { return tasks.filter((task) => task.status === TASK_STATUS.PENDING_ADMIN_PUBLISH && task.source === 'advisor') }
export function getPublishedTasks() { return tasks.filter((task) => task.status === TASK_STATUS.PUBLISHED) }
export function getTaskTypeText(type) { return TASK_TYPE_OPTIONS.find((option) => option.value === type)?.label || type || '--' }

export function adminDirectPublishTask(data, admin = { id: 'ADMIN001', name: '系统管理员' }) {
  if (!data?.title?.trim() || !data?.taskType || !data?.description?.trim() || !data?.requirement?.trim() || !data?.resultRequirement?.trim() || !data?.registrationDeadline || !data?.resultDeadline || Number(data?.hours) <= 0) return null
  const publishedAt = nowText()
  const task = normalizeTask({
    ...data,
    taskId: data.taskId || `TASK-ADMIN-${Date.now()}`,
    title: data.title.trim(),
    source: 'admin', publishSource: 'admin', publisherRole: 'admin', publisherName: admin.name,
    status: TASK_STATUS.PUBLISHED, submitTime: publishedAt, publishTime: publishedAt,
    adminConfirmTime: publishedAt, adminComment: '管理员直接发布任务。',
    applicants: [], selectedStudents: [], leaderId: '', leaderName: '',
  })
  tasks.push(task)
  return task
}

export function hasStudentApplied(taskId, studentId) {
  const task = getTask(taskId)
  return Boolean(task?.applicants?.some((applicant) => applicant.studentId === studentId))
}

export function getStudentAppliedTasks(studentId) {
  return tasks.filter((task) => task.applicants?.some((applicant) => applicant.studentId === studentId))
}

export function getTaskApplicants(taskId) {
  return getTask(taskId)?.applicants || []
}

export function getSelectedStudents(taskId) {
  return getTaskApplicants(taskId).filter((applicant) => applicant.selected || applicant.applyStatus === 'selected')
}

export function updateApplicantSelection(taskId, selections) {
  const task = getTask(taskId)
  if (!task || !Array.isArray(selections)) return { success: false, message: '任务或筛选数据不存在。' }
  const selectedCount = selections.filter((item) => item.selected).length
  if (!selectedCount) return { success: false, message: '至少选中 1 名学生才能完成筛选。' }
  const selectionMap = new Map(selections.map((item) => [item.studentId, item]))
  task.applicants.forEach((applicant) => {
    const selection = selectionMap.get(applicant.studentId)
    if (!selection) return
    applicant.selected = Boolean(selection.selected)
    applicant.applyStatus = applicant.selected ? 'selected' : 'not_selected'
    applicant.selectionComment = String(selection.selectionComment || '').trim()
    applicant.isLeader = false
  })
  task.selectedStudents = getSelectedStudents(taskId).map((student) => ({ ...student }))
  task.leaderId = ''
  task.leaderName = ''
  task.status = TASK_STATUS.SELECTING
  task.selectionTime = nowText()
  return { success: true, message: '筛选结果已保存，请继续指定队长。', task }
}

export function assignTaskLeader(taskId, studentId) {
  const task = getTask(taskId)
  if (!task) return { success: false, message: '任务不存在。' }
  const selectedStudents = getSelectedStudents(taskId)
  if (!selectedStudents.length) return { success: false, message: '请先筛选至少 1 名参与学生。' }
  const leader = selectedStudents.length === 1
    ? selectedStudents[0]
    : selectedStudents.find((student) => student.studentId === studentId)
  if (!leader) return { success: false, message: '必须从已选中学生中指定队长。' }
  task.applicants.forEach((applicant) => { applicant.isLeader = applicant.studentId === leader.studentId })
  task.leaderId = leader.studentId
  task.leaderName = leader.studentName
  task.selectedStudents = getSelectedStudents(taskId).map((student) => ({ ...student }))
  task.status = TASK_STATUS.LEADER_ASSIGNED
  task.leaderAssignTime = nowText()
  return { success: true, message: '队长指定成功。', task, leader }
}

export function getStudentSelectedTasks(studentId) {
  return tasks.filter((task) => task.applicants?.some((applicant) => applicant.studentId === studentId && (applicant.selected || applicant.applyStatus === 'selected')))
}

export function getStudentRejectedTasks(studentId) {
  return tasks.filter((task) => task.applicants?.some((applicant) => applicant.studentId === studentId && applicant.applyStatus === 'not_selected'))
}

export function getStudentApplyResult(taskId, studentId) {
  const task = getTask(taskId)
  const applicant = task?.applicants?.find((item) => item.studentId === studentId)
  if (!task || !applicant) return null
  return {
    taskId: task.taskId,
    applyTime: applicant.applyTime || '',
    applyStatus: applicant.applyStatus || 'applied',
    selected: Boolean(applicant.selected || applicant.applyStatus === 'selected'),
    isLeader: Boolean(applicant.isLeader || task.leaderId === studentId),
    selectionComment: applicant.selectionComment || '',
  }
}

export function getStudentTaskDetail(taskId, studentId) {
  const task = getTask(taskId)
  if (!task) return null
  const applicant = task.applicants?.find((item) => item.studentId === studentId)
  const selectedStudent = task.selectedStudents?.find((item) => item.studentId === studentId)
  if (!applicant && !selectedStudent && task.leaderId !== studentId) return null
  return { task, applicant: applicant || selectedStudent, applyResult: getStudentApplyResult(taskId, studentId), isLeader: task.leaderId === studentId || Boolean(applicant?.isLeader) }
}

export function getTaskTeamInfo(taskId, studentId) {
  const detail = getStudentTaskDetail(taskId, studentId)
  if (!detail) return { success: false, message: '未找到相关任务。' }
  const selected = detail.applicant?.selected || detail.applicant?.applyStatus === 'selected' || detail.task.leaderId === studentId
  if (!selected) return { success: false, message: '你未被选中，无法查看团队信息。', task: detail.task }
  const members = getSelectedStudents(taskId).map((student) => ({ ...student, isLeader: student.studentId === detail.task.leaderId || Boolean(student.isLeader) }))
  const leader = members.find((member) => member.isLeader) || null
  return { success: true, message: '', task: detail.task, leader, members }
}

export function markTaskResultSubmitted(taskId, studentId) {
  const task = getTask(taskId)
  if (!task || task.leaderId !== studentId) return null
  task.status = TASK_STATUS.RESULT_SUBMITTED
  return task
}

export function applyTask(taskId, student) {
  const task = getTask(taskId)
  if (!task) return { success: false, message: '任务不存在。' }
  if (task.status !== TASK_STATUS.PUBLISHED) return { success: false, message: '当前任务尚未发布，无法报名。' }
  const deadline = new Date(String(task.registrationDeadline).replace(' ', 'T')).getTime()
  if (!Number.isFinite(deadline) || Date.now() >= deadline) return { success: false, message: '报名已截止。' }
  if (!student?.studentId) return { success: false, message: '学生信息不完整，无法报名。' }
  if (hasStudentApplied(taskId, student.studentId)) return { success: false, message: '你已报名该任务，请勿重复报名。' }
  const applicant = {
    studentId: student.studentId,
    studentName: student.studentName || student.name || '',
    college: student.college || '',
    major: student.major || '',
    applyTime: nowText(),
    applyStatus: 'applied',
    selected: false,
  }
  task.applicants.push(applicant)
  return { success: true, message: '报名成功，请等待指导老师筛选。', applicant, task }
}

export function saveTaskDraft(data) {
  const existing = data.taskId ? getTask(data.taskId) : null
  if (existing && ![TASK_STATUS.DRAFT, TASK_STATUS.PUBLISH_REJECTED].includes(existing.status)) return null
  const next = normalizeTask({ ...existing, ...data, status: TASK_STATUS.DRAFT, adminComment: existing?.status === TASK_STATUS.PUBLISH_REJECTED ? existing.adminComment : '', adminConfirmTime: existing?.status === TASK_STATUS.PUBLISH_REJECTED ? existing.adminConfirmTime : '' })
  if (existing) Object.assign(existing, next); else tasks.push(next)
  return existing || next
}

export function submitTaskForPublish(data) {
  const existing = data.taskId ? getTask(data.taskId) : null
  if (existing && ![TASK_STATUS.DRAFT, TASK_STATUS.PUBLISH_REJECTED].includes(existing.status)) return null
  const next = normalizeTask({ ...existing, ...data, status: TASK_STATUS.PENDING_ADMIN_PUBLISH, submitTime: nowText(), publishTime: '', adminComment: '', adminConfirmTime: '' })
  if (existing) Object.assign(existing, next); else tasks.push(next)
  return existing || next
}

export function adminApproveTaskPublish(taskId, comment = '') {
  const task = getTask(taskId)
  if (!task || task.status !== TASK_STATUS.PENDING_ADMIN_PUBLISH || task.source !== 'advisor') return null
  const confirmedAt = nowText()
  task.status = TASK_STATUS.PUBLISHED
  task.adminComment = comment.trim()
  task.adminConfirmTime = confirmedAt
  task.publishTime = confirmedAt
  return task
}

export function adminRejectTaskPublish(taskId, comment) {
  const task = getTask(taskId)
  if (!task || task.status !== TASK_STATUS.PENDING_ADMIN_PUBLISH || task.source !== 'advisor' || !comment?.trim()) return null
  task.status = TASK_STATUS.PUBLISH_REJECTED
  task.adminComment = comment.trim()
  task.adminConfirmTime = nowText()
  task.publishTime = ''
  return task
}

function createBatchResult(taskIds) {
  return { total: taskIds.length, success: 0, failed: 0, failedItems: [] }
}

export function batchApproveTaskPublish(taskIds, comment = '') {
  const ids = [...new Set(taskIds)]
  const result = createBatchResult(ids)
  ids.forEach((taskId) => {
    const task = getTask(taskId)
    let reason = ''
    if (!task) reason = '任务不存在'
    else if (task.source !== 'advisor') reason = '仅支持确认指导老师发布的任务'
    else if (task.status !== TASK_STATUS.PENDING_ADMIN_PUBLISH) reason = '当前状态不可确认发布'
    if (reason) { result.failed += 1; result.failedItems.push({ taskId, reason }); return }
    adminApproveTaskPublish(taskId, comment)
    result.success += 1
  })
  return result
}

export function batchRejectTaskPublish(taskIds, comment) {
  const ids = [...new Set(taskIds)]
  const result = createBatchResult(ids)
  ids.forEach((taskId) => {
    const task = getTask(taskId)
    let reason = ''
    if (!comment?.trim()) reason = '批量驳回必须填写处理意见'
    else if (!task) reason = '任务不存在'
    else if (task.source !== 'advisor') reason = '仅支持驳回指导老师发布的任务'
    else if (task.status !== TASK_STATUS.PENDING_ADMIN_PUBLISH) reason = '当前状态不可驳回'
    if (reason) { result.failed += 1; result.failedItems.push({ taskId, reason }); return }
    adminRejectTaskPublish(taskId, comment)
    result.success += 1
  })
  return result
}
