export const TASK_STATUS = Object.freeze({
  DRAFT: 'draft',
  PENDING_ADMIN_PUBLISH: 'pending_admin_publish',
  PUBLISHED: 'published',
  PUBLISH_REJECTED: 'publish_rejected',
  CLOSED: 'closed',
  SELECTING: 'selecting',
  SELECTED: 'selected',
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

const tasks = [
  {
    taskId: 'TASK-2026-001', title: '校园数字化志愿服务', taskType: 'volunteer_service',
    description: '协助整理校园活动数字档案，并完成现场志愿服务。', requirement: '责任心强，能够按时参加线下活动。',
    resultRequirement: '提交服务记录、活动照片及不少于 800 字的总结。', advisorId: 'T001', advisorName: '张明', source: 'advisor',
    registrationDeadline: '2026-08-20 18:00', attachments: [{ id: 'TASK-ATT-001', name: '任务安排说明.pdf', type: 'PDF', size: '1.2 MB', uploadedAt: '2026-07-20 10:15' }],
    status: TASK_STATUS.PENDING_ADMIN_PUBLISH, submitTime: '2026-07-20 10:20', publishTime: '', adminComment: '', adminConfirmTime: '',
    applicants: [], selectedStudents: [], leaderId: '', leaderName: '',
  },
  {
    taskId: 'TASK-2026-002', title: '创新项目调研助手', taskType: 'innovation',
    description: '参与创新创业项目的用户访谈和竞品资料整理。', requirement: '具备基础调研与文档整理能力。',
    resultRequirement: '提交调研纪要、竞品分析表及个人工作总结。', advisorId: 'T001', advisorName: '张明', source: 'advisor',
    registrationDeadline: '2026-08-25 18:00', attachments: [], status: TASK_STATUS.PUBLISH_REJECTED,
    submitTime: '2026-07-18 14:30', publishTime: '', adminComment: '报名条件描述过于宽泛，请补充具体能力要求。', adminConfirmTime: '2026-07-19 09:15',
    applicants: [], selectedStudents: [], leaderId: '', leaderName: '',
  },
  {
    taskId: 'TASK-2026-003', title: '社区科普活动策划', taskType: 'social_practice',
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
  const normalized = { taskId, title: '', taskType: '', description: '', requirement: '', resultRequirement: '', advisorId: '', advisorName: '', source: 'advisor', registrationDeadline: '', attachments: [], status: TASK_STATUS.DRAFT, submitTime: '', publishTime: '', adminComment: '', adminConfirmTime: '', applicants: [], selectedStudents: [], leaderId: '', leaderName: '', ...task, taskId }
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
export function getAdvisorTasks(advisorId) { return tasks.filter((task) => task.advisorId === advisorId && task.source === 'advisor') }
export function getPendingAdminPublishTasks() { return tasks.filter((task) => task.status === TASK_STATUS.PENDING_ADMIN_PUBLISH) }
export function getPublishedTasks() { return tasks.filter((task) => task.status === TASK_STATUS.PUBLISHED) }
export function getTaskTypeText(type) { return TASK_TYPE_OPTIONS.find((option) => option.value === type)?.label || type || '--' }

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
