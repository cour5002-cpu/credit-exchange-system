export const APPLICATION_STATUS = Object.freeze({
  DRAFT: 'draft',
  SUBMITTED: 'submitted',
  PENDING_ADVISOR: 'pending_advisor',
  ADVISOR_APPROVED: 'advisor_approved',
  ADVISOR_REJECTED: 'advisor_rejected',
  PENDING_ADMIN_ACCEPT: 'pending_admin_accept',
  ADMIN_ACCEPTED: 'admin_accepted',
  PENDING_REVIEWER: 'pending_reviewer',
  REVIEWER_APPROVED: 'reviewer_approved',
  REVIEWER_MODIFIED_APPROVED: 'reviewer_modified_approved',
  REVIEWER_REJECTED: 'reviewer_rejected',
  PENDING_ADMIN_FINAL: 'pending_admin_final',
  FINAL_APPROVED: 'final_approved',
  FINAL_REJECTED: 'final_rejected',
})

export const APPLICATION_STAGE = Object.freeze({
  STUDENT: 'student',
  ADVISOR: 'advisor',
  ADMIN_ACCEPT: 'admin_accept',
  REVIEWER: 'reviewer',
  ADMIN_FINAL: 'admin_final',
  FINISHED: 'finished',
})

export const currentReviewerId = ref('reviewer001')

export const mockReviewers = [
  { reviewerId: 'reviewer001', reviewerName: '刘敏', college: '计算机学院', direction: '项目成果与技术实践', get pendingCount() { return getReviewerPendingCount(this.reviewerId) } },
  { reviewerId: 'reviewer002', reviewerName: '孙伟', college: '管理学院', direction: '创新创业与社会实践', get pendingCount() { return getReviewerPendingCount(this.reviewerId) } },
  { reviewerId: 'reviewer003', reviewerName: '周岚', college: '校团委', direction: '志愿服务与综合实践', get pendingCount() { return getReviewerPendingCount(this.reviewerId) } },
]

const statusStageMap = {
  draft: APPLICATION_STAGE.STUDENT,
  submitted: APPLICATION_STAGE.STUDENT,
  pending_advisor: APPLICATION_STAGE.ADVISOR,
  advisor_approved: APPLICATION_STAGE.ADVISOR,
  advisor_rejected: APPLICATION_STAGE.FINISHED,
  pending_admin_accept: APPLICATION_STAGE.ADMIN_ACCEPT,
  admin_accepted: APPLICATION_STAGE.ADMIN_ACCEPT,
  pending_reviewer: APPLICATION_STAGE.REVIEWER,
  reviewer_approved: APPLICATION_STAGE.REVIEWER,
  reviewer_modified_approved: APPLICATION_STAGE.REVIEWER,
  reviewer_rejected: APPLICATION_STAGE.FINISHED,
  pending_admin_final: APPLICATION_STAGE.ADMIN_FINAL,
  final_approved: APPLICATION_STAGE.FINISHED,
  final_rejected: APPLICATION_STAGE.FINISHED,
}

const sourceTextMap = {
  self: '学生自主申请',
  task: '任务成果申请',
}

const applyTypeTextMap = {
  with_result: '有成果申请',
  without_result: '无成果申请',
}

function nowText() {
  const date = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function resolveReviewerId(data) {
  if (data.reviewerId) return data.reviewerId
  if (data.reviewer?.id) return data.reviewer.id
  if (data.reviewer?.name === '赵审核老师') return 'reviewer001'
  return mockReviewers.find((reviewer) => reviewer.reviewerName === data.reviewer?.name)?.reviewerId ?? ''
}

function createApplication(data) {
  const status = data.status ?? APPLICATION_STATUS.PENDING_ADVISOR

  return {
    id: '',
    title: '',
    studentName: '',
    studentId: '',
    source: 'self',
    sourceText: '',
    applyType: 'with_result',
    applyTypeText: '',
    requestedHours: 0,
    taskId: '',
    taskTitle: '',
    submitTime: '',

    captainId: '',
    currentUserId: '',
    members: [],

    mainAdvisor: null,
    viewAdvisors: [],
    advisorStatus: 'pending',
    advisorComment: '',
    advisorConfirmTime: '',

    adminAcceptStatus: 'pending',
    adminAcceptComment: '',
    adminAcceptTime: '',

    reviewer: null,
    reviewerId: '',
    reviewStatus: 'pending',
    originalHours: null,
    recognizedHours: null,
    reviewResult: '',
    reviewComment: '',
    reviewTime: '',

    finalStatus: 'pending',
    finalComment: '',
    finalConfirmTime: '',

    attachments: [],
    ...data,
    reviewerId: resolveReviewerId(data),
    sourceText: data.sourceText ?? sourceTextMap[data.source] ?? '',
    applyTypeText: data.applyTypeText ?? applyTypeTextMap[data.applyType] ?? '',
    status,
    stage: data.stage ?? statusStageMap[status],
  }
}

const applications = [
  createApplication({
    id: 'APP-2026-001',
    title: '校园志愿服务课时申请',
    studentName: '张三',
    studentId: '2024001',
    source: 'self',
    applyType: 'with_result',
    requestedHours: 16,
    submitTime: '2026-07-15 09:30',
    captainId: 'stu001',
    currentUserId: 'stu001',
    members: [
      { id: 'stu001', name: '张三', studentId: '2024001', role: 'captain' },
      { id: 'stu002', name: '周然', studentId: '2023101022', role: 'member' },
    ],
    mainAdvisor: { id: 'T001', name: '张明', department: '计算机学院' },
    viewAdvisors: [{ id: 'T004', name: '陈强', department: '校团委' }],
    attachments: [
      { id: 'ATT-001', name: '志愿服务成果报告.pdf', type: 'PDF' },
      { id: 'ATT-002', name: '团队成员承诺书.docx', type: 'Word' },
    ],
  }),
  createApplication({
    id: 'APP-2026-002',
    title: '创新创业项目成果申请',
    studentName: '王晨',
    studentId: '2022102036',
    source: 'task',
    applyType: 'with_result',
    requestedHours: 20,
    taskId: 'TASK-002',
    taskTitle: '创新创业项目路演',
    submitTime: '2026-07-14 16:20',
    captainId: 'stu010',
    currentUserId: 'stu010',
    members: [{ id: 'stu010', name: '王晨', studentId: '2022102036', role: 'captain' }],
    mainAdvisor: { id: 'T002', name: '李华', department: '管理学院' },
    viewAdvisors: [],
    status: APPLICATION_STATUS.PENDING_ADMIN_ACCEPT,
    advisorStatus: 'approved',
    advisorComment: '成果材料完整，确认通过。',
    advisorConfirmTime: '2026-07-14 16:55',
    attachments: [{ id: 'ATT-003', name: '项目成果文件.pdf', type: 'PDF' }],
  }),
  createApplication({
    id: 'APP-2026-003',
    title: '学科竞赛成果申请',
    studentName: '陈思远',
    studentId: '2023103058',
    source: 'task',
    applyType: 'with_result',
    requestedHours: 32,
    taskId: 'TASK-003',
    taskTitle: '省级电子设计竞赛',
    submitTime: '2026-07-13 11:05',
    captainId: 'stu020',
    currentUserId: 'stu020',
    members: [{ id: 'stu020', name: '陈思远', studentId: '2023103058', role: 'captain' }],
    mainAdvisor: { id: 'T004', name: '陈强', department: '校团委' },
    viewAdvisors: [],
    status: APPLICATION_STATUS.PENDING_REVIEWER,
    advisorStatus: 'approved',
    advisorComment: '竞赛成果信息属实。',
    advisorConfirmTime: '2026-07-13 11:40',
    adminAcceptStatus: 'accepted',
    adminAcceptComment: '材料齐全，同意受理。',
    adminAcceptTime: '2026-07-13 14:10',
    reviewerId: 'reviewer001',
    reviewer: { id: 'reviewer001', name: '刘敏', college: '计算机学院', direction: '项目成果与技术实践' },
    attachments: [{ id: 'ATT-004', name: '竞赛获奖证书.pdf', type: 'PDF' }],
  }),
  createApplication({
    id: 'APP-2026-004',
    title: '社会实践成果申请',
    studentName: '赵可欣',
    studentId: '2022104107',
    source: 'self',
    applyType: 'without_result',
    requestedHours: 12,
    submitTime: '2026-07-12 14:45',
    captainId: 'stu030',
    currentUserId: 'stu030',
    members: [{ id: 'stu030', name: '赵可欣', studentId: '2022104107', role: 'captain' }],
    mainAdvisor: { id: 'T003', name: '王芳', department: '艺术学院' },
    viewAdvisors: [],
    status: APPLICATION_STATUS.PENDING_ADMIN_FINAL,
    advisorStatus: 'approved',
    advisorComment: '确认学生参与情况。',
    advisorConfirmTime: '2026-07-12 15:10',
    adminAcceptStatus: 'accepted',
    adminAcceptComment: '同意受理。',
    adminAcceptTime: '2026-07-13 09:00',
    reviewerId: 'reviewer001',
    reviewer: { id: 'reviewer001', name: '刘敏', college: '计算机学院', direction: '项目成果与技术实践' },
    reviewStatus: 'modified_approved',
    originalHours: 12,
    recognizedHours: 10,
    reviewResult: 'modified_approved',
    reviewComment: '部分工作量重复，调整为 10 课时。',
    reviewTime: '2026-07-14 10:20',
    attachments: [],
  }),
  createApplication({
    id: 'APP-2026-005',
    title: '校园数据分析项目成果认定',
    studentName: '张三',
    studentId: '2024001',
    source: 'task',
    applyType: 'with_result',
    requestedHours: 18,
    taskId: 'TASK-001',
    taskTitle: '校园数据分析项目',
    submitTime: '2026-07-10 09:20',
    captainId: 'stu001',
    currentUserId: 'stu001',
    members: [
      { id: 'stu001', name: '张三', studentId: '2024001', role: 'captain' },
      { id: 'stu002', name: '李四', studentId: '2024002', role: 'member' },
    ],
    mainAdvisor: { id: 'T001', name: '张明', department: '计算机学院' },
    viewAdvisors: [],
    status: APPLICATION_STATUS.FINAL_APPROVED,
    advisorStatus: 'approved',
    advisorComment: '项目成果和成员信息确认无误。',
    advisorConfirmTime: '2026-07-10 10:15',
    adminAcceptStatus: 'accepted',
    adminAcceptComment: '材料完整，已受理并分配。',
    adminAcceptTime: '2026-07-10 14:30',
    reviewerId: 'reviewer001',
    reviewer: { id: 'reviewer001', name: '刘敏', college: '计算机学院', direction: '项目成果与技术实践' },
    reviewStatus: 'modified_approved',
    originalHours: 18,
    recognizedHours: 16,
    reviewResult: 'modified_approved',
    reviewComment: '扣除重复工作量后认定 16 课时。',
    reviewTime: '2026-07-11 09:40',
    finalStatus: 'approved',
    finalComment: '最终确认通过，认定 16 课时。',
    finalConfirmTime: '2026-07-11 15:20',
    attachments: [{ id: 'ATT-005', name: '项目成果认定材料.pdf', type: 'PDF', uploadedAt: '2026-07-10 09:15' }],
  }),
]

function getReviewerPendingCount(reviewerId) {
  return applications.filter((application) =>
    application.status === APPLICATION_STATUS.PENDING_REVIEWER
    && application.reviewerId === reviewerId,
  ).length
}

function findApplication(id) {
  return applications.find((application) => application.id === id)
}

function updateStatus(application, status) {
  application.status = status
  application.stage = statusStageMap[status]
  return application
}

export function getApplications() {
  return applications
}

export function addApplication(application) {
  const addedApplication = createApplication({
    ...application,
    id: application.id || `APP-${Date.now()}`,
    submitTime: application.submitTime || nowText(),
    status: APPLICATION_STATUS.PENDING_ADVISOR,
    stage: APPLICATION_STAGE.ADVISOR,
    advisorStatus: 'pending',
  })
  applications.push(addedApplication)
  return addedApplication
}

export function advisorApprove(id, comment = '') {
  const application = findApplication(id)
  if (!application) return null
  application.advisorStatus = 'approved'
  application.advisorComment = comment
  application.advisorConfirmTime = nowText()
  return updateStatus(application, APPLICATION_STATUS.PENDING_ADMIN_ACCEPT)
}

export function advisorReject(id, comment = '') {
  const application = findApplication(id)
  if (!application) return null
  application.advisorStatus = 'rejected'
  application.advisorComment = comment
  application.advisorConfirmTime = nowText()
  return updateStatus(application, APPLICATION_STATUS.ADVISOR_REJECTED)
}

function getDefaultReviewer() {
  return mockReviewers.reduce((selected, reviewer) =>
    reviewer.pendingCount < selected.pendingCount ? reviewer : selected,
  )
}

function assignReviewer(application, reviewer) {
  const matchedReviewer = typeof reviewer === 'string'
    ? mockReviewers.find((item) => item.reviewerId === reviewer)
    : mockReviewers.find((item) => item.reviewerId === reviewer?.reviewerId)
  const assignedReviewer = matchedReviewer ?? getDefaultReviewer()

  application.reviewerId = assignedReviewer.reviewerId
  application.reviewer = {
    id: assignedReviewer.reviewerId,
    name: assignedReviewer.reviewerName,
    college: assignedReviewer.college,
    direction: assignedReviewer.direction,
  }
}

function writeReviewerIdentity(application, reviewerId) {
  const reviewer = mockReviewers.find((item) => item.reviewerId === reviewerId)
  if (!reviewer) return
  application.reviewerId = reviewer.reviewerId
  application.reviewer = {
    id: reviewer.reviewerId,
    name: reviewer.reviewerName,
    college: reviewer.college,
    direction: reviewer.direction,
  }
}

export function adminAccept(id, comment = '', reviewer = null) {
  const application = findApplication(id)
  if (!application) return null
  assignReviewer(application, reviewer)
  application.adminAcceptStatus = 'accepted'
  application.adminAcceptComment = comment
  application.adminAcceptTime = nowText()
  return updateStatus(application, APPLICATION_STATUS.PENDING_REVIEWER)
}

export function reviewerApprove(id, recognizedHours, comment = '', reviewerId = '') {
  const application = findApplication(id)
  if (!application) return null
  writeReviewerIdentity(application, reviewerId || application.reviewerId)
  application.reviewStatus = 'approved'
  application.originalHours = application.requestedHours
  application.recognizedHours = application.requestedHours
  application.reviewResult = 'approved'
  application.reviewComment = comment
  application.reviewTime = nowText()
  return updateStatus(application, APPLICATION_STATUS.PENDING_ADMIN_FINAL)
}

export function reviewerModifiedApprove(id, recognizedHours, comment = '', reviewerId = '') {
  const application = findApplication(id)
  if (!application) return null
  writeReviewerIdentity(application, reviewerId || application.reviewerId)
  application.reviewStatus = 'modified_approved'
  application.originalHours = application.requestedHours
  application.recognizedHours = recognizedHours
  application.reviewResult = 'modified_approved'
  application.reviewComment = comment
  application.reviewTime = nowText()
  return updateStatus(application, APPLICATION_STATUS.PENDING_ADMIN_FINAL)
}

export function reviewerReject(id, comment = '', reviewerId = '') {
  const application = findApplication(id)
  if (!application) return null
  writeReviewerIdentity(application, reviewerId || application.reviewerId)
  application.reviewStatus = 'rejected'
  application.originalHours = application.requestedHours
  application.recognizedHours = 0
  application.reviewResult = 'rejected'
  application.reviewComment = comment
  application.reviewTime = nowText()
  return updateStatus(application, APPLICATION_STATUS.REVIEWER_REJECTED)
}

export function finalApprove(id, comment = '') {
  const application = findApplication(id)
  if (!application) return null
  application.finalStatus = 'approved'
  application.finalComment = comment
  application.finalConfirmTime = nowText()
  return updateStatus(application, APPLICATION_STATUS.FINAL_APPROVED)
}

export function finalReject(id, comment = '') {
  const application = findApplication(id)
  if (!application) return null
  application.finalStatus = 'rejected'
  application.finalComment = comment
  application.finalConfirmTime = nowText()
  return updateStatus(application, APPLICATION_STATUS.FINAL_REJECTED)
}

export function getAdvisorPendingApplications() {
  return applications.filter((application) => application.status === APPLICATION_STATUS.PENDING_ADVISOR)
}

export function getAdminAcceptApplications() {
  return applications.filter((application) => application.status === APPLICATION_STATUS.PENDING_ADMIN_ACCEPT)
}

export function getReviewerPendingApplications(reviewerId = '') {
  return applications.filter((application) =>
    application.status === APPLICATION_STATUS.PENDING_REVIEWER
    && (!reviewerId || application.reviewerId === reviewerId),
  )
}

export function getAdminFinalApplications() {
  return applications.filter((application) => application.status === APPLICATION_STATUS.PENDING_ADMIN_FINAL)
}

export function getFinishedApplications() {
  const finishedStatuses = new Set([
    APPLICATION_STATUS.ADVISOR_REJECTED,
    APPLICATION_STATUS.REVIEWER_REJECTED,
    APPLICATION_STATUS.FINAL_APPROVED,
    APPLICATION_STATUS.FINAL_REJECTED,
  ])
  return applications.filter((application) => finishedStatuses.has(application.status))
}
import { ref } from 'vue'
