export const APPLICATION_STATUS = Object.freeze({
  DRAFT: 'draft',
  SUBMITTED: 'submitted',
  PENDING_ADVISOR: 'pending_advisor',
  PENDING_RESULT: 'pending_result',
  NEED_SUPPLEMENT_RESULT: 'need_supplement_result',
  PENDING_MATERIAL: 'pending_material',
  MATERIAL_SUBMITTED: 'material_submitted',
  SUPPLEMENT_REJECTED: 'supplement_rejected',
  PENDING_ADVISOR_EXTENSION: 'pending_advisor_extension',
  PENDING_ADMIN_SPECIAL_EXTENSION: 'pending_admin_special_extension',
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
  pending_result: APPLICATION_STAGE.STUDENT,
  waiting_result: APPLICATION_STAGE.STUDENT,
  need_supplement_result: APPLICATION_STAGE.STUDENT,
  pending_material: APPLICATION_STAGE.STUDENT,
  material_submitted: APPLICATION_STAGE.ADVISOR,
  supplement_rejected: APPLICATION_STAGE.STUDENT,
  pending_advisor_extension: APPLICATION_STAGE.ADVISOR,
  pending_admin_special_extension: APPLICATION_STAGE.ADMIN_ACCEPT,
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
  task_result: '任务成果申请',
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

let applicationSequence = 0
function nextApplicationId() {
  applicationSequence += 1
  return `APP-${Date.now()}-${applicationSequence}`
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
    applicationId: '',
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
    resultDescription: '', resultMaterials: [], proofMaterials: [], expectedResultDate: '',
    supplementTime: '', supplementCount: 0, allowResultSupplement: false, timelineEvents: [],
    extensionApplied: false, extensionType: '', originalExpectedResultTime: '', newExpectedResultTime: '',
    extensionReason: '', extensionMaterials: [], extensionSubmitTime: '', extensionStatus: '',
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
  const applicationId = application.applicationId || application.id || nextApplicationId()
  const addedApplication = createApplication({
    ...application,
    id: applicationId,
    applicationId,
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
  if (application.applyType === 'without_result' && !application.resultMaterials?.length) {
    application.allowResultSupplement = true
    return updateStatus(application, APPLICATION_STATUS.PENDING_MATERIAL)
  }
  return updateStatus(application, APPLICATION_STATUS.PENDING_ADMIN_ACCEPT)
}

export function advisorReject(id, comment = '') {
  const application = findApplication(id)
  if (!application) return null
  application.advisorStatus = 'rejected'
  application.advisorComment = comment
  application.advisorConfirmTime = nowText()
  application.allowResultSupplement = true
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
  application.allowResultSupplement = true
  return updateStatus(application, APPLICATION_STATUS.REVIEWER_REJECTED)
}

const supplementStatuses = new Set([APPLICATION_STATUS.PENDING_RESULT, APPLICATION_STATUS.NEED_SUPPLEMENT_RESULT, APPLICATION_STATUS.PENDING_MATERIAL, APPLICATION_STATUS.SUPPLEMENT_REJECTED, 'waiting_result'])

export function canSupplementResult(applicationOrId) {
  const application = typeof applicationOrId === 'string' ? findApplication(applicationOrId) : applicationOrId
  if (!application) return false
  if (Number(application.supplementCount || 0) >= 1 && application.status !== APPLICATION_STATUS.SUPPLEMENT_REJECTED) return false
  if (application.resultMaterials?.length && application.status !== APPLICATION_STATUS.SUPPLEMENT_REJECTED) return false
  const rejectedAndRetryable = application.allowResultSupplement === true
    && [APPLICATION_STATUS.ADVISOR_REJECTED, APPLICATION_STATUS.REVIEWER_REJECTED, APPLICATION_STATUS.SUPPLEMENT_REJECTED].includes(application.status)
  if (rejectedAndRetryable) return true
  if (application.applyType !== 'without_result' || !supplementStatuses.has(application.status)) return false
  const deadline = application.expectedResultDate || application.newExpectedResultTime
  if (!deadline) return false
  const today = new Date(); const pad = (value) => String(value).padStart(2, '0')
  const todayText = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`
  return todayText <= deadline
}

export function supplementApplicationResult(id, payload) {
  const application = findApplication(id)
  if (!canSupplementResult(application) || !payload?.resultDescription?.trim() || !payload?.resultMaterials?.length) return null
  const supplementTime = nowText()
  application.resultDescription = payload.resultDescription.trim()
  application.resultMaterials = payload.resultMaterials.map((file) => ({ ...file }))
  application.proofMaterials = (payload.proofMaterials || []).map((file) => ({ ...file }))
  application.attachments = [...application.resultMaterials, ...application.proofMaterials].map((file) => ({ ...file }))
  application.supplementTime = supplementTime
  application.supplementCount = Number(application.supplementCount || 0) + 1
  application.allowResultSupplement = false
  application.supplementAdvisorStatus = 'pending'
  application.supplementAdvisorComment = ''
  application.supplementAdvisorConfirmTime = ''
  application.timelineEvents = [...(application.timelineEvents || []), { type: 'result_supplemented', title: '学生已补交成果，等待指导老师再次确认。', time: supplementTime }]
  return updateStatus(application, APPLICATION_STATUS.MATERIAL_SUBMITTED)
}

export function getAdvisorPendingSupplementApplications(advisorId = '') {
  return applications.filter((application) => application.status === APPLICATION_STATUS.MATERIAL_SUBMITTED && (!advisorId || application.mainAdvisor?.id === advisorId))
}

export function advisorApproveSupplement(id, comment = '') {
  const application = findApplication(id)
  if (!application || application.status !== APPLICATION_STATUS.MATERIAL_SUBMITTED) return null
  application.supplementAdvisorStatus = 'approved'
  application.supplementAdvisorComment = comment.trim()
  application.supplementAdvisorConfirmTime = nowText()
  application.allowResultSupplement = false
  return updateStatus(application, APPLICATION_STATUS.PENDING_ADMIN_ACCEPT)
}

export function advisorRejectSupplement(id, comment = '') {
  const application = findApplication(id)
  if (!application || application.status !== APPLICATION_STATUS.MATERIAL_SUBMITTED || !comment.trim()) return null
  application.supplementAdvisorStatus = 'rejected'
  application.supplementAdvisorComment = comment.trim()
  application.supplementAdvisorConfirmTime = nowText()
  application.allowResultSupplement = true
  return updateStatus(application, APPLICATION_STATUS.SUPPLEMENT_REJECTED)
}

const extensionAllowedStatuses = new Set([APPLICATION_STATUS.PENDING_MATERIAL, APPLICATION_STATUS.PENDING_RESULT, 'waiting_result'])

export function canApplyExtension(applicationOrId) {
  const application = typeof applicationOrId === 'string' ? findApplication(applicationOrId) : applicationOrId
  return Boolean(application
    && application.applyType === 'without_result'
    && extensionAllowedStatuses.has(application.status)
    && !application.resultMaterials?.length
    && !application.extensionApplied)
}

export function getExtensionType(originalTime, newTime) {
  const original = new Date(`${originalTime}T00:00:00`)
  const next = new Date(`${newTime}T00:00:00`)
  if (Number.isNaN(original.getTime()) || Number.isNaN(next.getTime()) || next <= original) return ''
  const days = Math.ceil((next - original) / 86400000)
  return days <= 30 ? 'normal' : 'special'
}

export function submitExtensionApplication(id, payload) {
  const application = findApplication(id)
  if (!canApplyExtension(application) || !payload?.newExpectedResultTime || !payload?.extensionReason?.trim()) return null
  const originalExpectedResultTime = application.expectedResultDate || application.originalExpectedResultTime
  const extensionType = getExtensionType(originalExpectedResultTime, payload.newExpectedResultTime)
  if (!extensionType) return null
  const extensionSubmitTime = nowText()
  application.extensionApplied = true
  application.extensionType = extensionType
  application.originalExpectedResultTime = originalExpectedResultTime
  application.newExpectedResultTime = payload.newExpectedResultTime
  application.extensionReason = payload.extensionReason.trim()
  application.extensionMaterials = (payload.extensionMaterials || []).map((file) => ({ ...file }))
  application.extensionSubmitTime = extensionSubmitTime
  application.extensionStatus = extensionType === 'normal' ? 'pending_advisor' : 'pending_admin'
  application.timelineEvents = [...(application.timelineEvents || []), { type: 'extension_submitted', title: '学生已提交延期申请，等待处理。', time: extensionSubmitTime }]
  return updateStatus(application, extensionType === 'normal' ? APPLICATION_STATUS.PENDING_ADVISOR_EXTENSION : APPLICATION_STATUS.PENDING_ADMIN_SPECIAL_EXTENSION)
}

export function approveExtensionApplication(id, comment = '') {
  const application = findApplication(id)
  const validStatus = application?.extensionType === 'normal'
    ? APPLICATION_STATUS.PENDING_ADVISOR_EXTENSION
    : APPLICATION_STATUS.PENDING_ADMIN_SPECIAL_EXTENSION
  if (!application || application.status !== validStatus) return null
  application.extensionStatus = 'approved'
  application.extensionComment = comment.trim()
  application.extensionConfirmTime = nowText()
  application.expectedResultDate = application.newExpectedResultTime
  application.timelineEvents = [...(application.timelineEvents || []), { type: 'extension_approved', title: '延期申请已通过，请在新的预计时间前补交成果。', time: application.extensionConfirmTime }]
  return updateStatus(application, APPLICATION_STATUS.PENDING_MATERIAL)
}

export function getAdvisorPendingNormalExtensions(advisorId = '') {
  return applications.filter((application) => application.status === APPLICATION_STATUS.PENDING_ADVISOR_EXTENSION
    && application.extensionType === 'normal'
    && (!advisorId || application.mainAdvisor?.id === advisorId))
}

export function approveNormalExtension(id, comment = '') {
  const application = findApplication(id)
  if (!application || application.status !== APPLICATION_STATUS.PENDING_ADVISOR_EXTENSION || application.extensionType !== 'normal') return null
  const confirmTime = nowText()
  application.extensionStatus = 'approved'
  application.extensionAdvisorComment = comment.trim()
  application.extensionAdvisorConfirmTime = confirmTime
  application.extensionComment = comment.trim()
  application.extensionConfirmTime = confirmTime
  application.expectedResultDate = application.newExpectedResultTime
  application.expectedResultTime = application.newExpectedResultTime
  application.timelineEvents = [...(application.timelineEvents || []), { type: 'normal_extension_approved', title: `指导老师已通过普通延期申请，新的成果提交时间为 ${application.newExpectedResultTime}。`, time: confirmTime }]
  return updateStatus(application, APPLICATION_STATUS.PENDING_MATERIAL)
}

export function rejectNormalExtension(id, comment = '') {
  const application = findApplication(id)
  if (!application || application.status !== APPLICATION_STATUS.PENDING_ADVISOR_EXTENSION || application.extensionType !== 'normal' || !comment.trim()) return null
  const confirmTime = nowText()
  application.extensionStatus = 'rejected'
  application.extensionAdvisorComment = comment.trim()
  application.extensionAdvisorConfirmTime = confirmTime
  application.extensionComment = comment.trim()
  application.extensionConfirmTime = confirmTime
  application.timelineEvents = [...(application.timelineEvents || []), { type: 'normal_extension_rejected', title: '指导老师已驳回普通延期申请。', time: confirmTime, comment: comment.trim() }]
  return updateStatus(application, APPLICATION_STATUS.PENDING_MATERIAL)
}

export function getAdminPendingSpecialExtensions() {
  return applications.filter((application) => application.status === APPLICATION_STATUS.PENDING_ADMIN_SPECIAL_EXTENSION
    && application.extensionType === 'special')
}

export function approveSpecialExtension(id, comment = '') {
  const application = findApplication(id)
  if (!application || application.status !== APPLICATION_STATUS.PENDING_ADMIN_SPECIAL_EXTENSION || application.extensionType !== 'special') return null
  const confirmTime = nowText()
  application.extensionStatus = 'approved'
  application.extensionAdminComment = comment.trim()
  application.extensionAdminConfirmTime = confirmTime
  application.extensionComment = comment.trim()
  application.extensionConfirmTime = confirmTime
  application.expectedResultDate = application.newExpectedResultTime
  application.expectedResultTime = application.newExpectedResultTime
  application.timelineEvents = [...(application.timelineEvents || []), { type: 'special_extension_approved', title: `管理员已通过特殊延期申请，新的成果提交时间为 ${application.newExpectedResultTime}。`, time: confirmTime }]
  return updateStatus(application, APPLICATION_STATUS.PENDING_MATERIAL)
}

export function rejectSpecialExtension(id, comment = '') {
  const application = findApplication(id)
  if (!application || application.status !== APPLICATION_STATUS.PENDING_ADMIN_SPECIAL_EXTENSION || application.extensionType !== 'special' || !comment.trim()) return null
  const confirmTime = nowText()
  application.extensionStatus = 'rejected'
  application.extensionAdminComment = comment.trim()
  application.extensionAdminConfirmTime = confirmTime
  application.extensionComment = comment.trim()
  application.extensionConfirmTime = confirmTime
  application.timelineEvents = [...(application.timelineEvents || []), { type: 'special_extension_rejected', title: '管理员已驳回特殊延期申请。', time: confirmTime, comment: comment.trim() }]
  return updateStatus(application, APPLICATION_STATUS.PENDING_MATERIAL)
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

export function updateApplicationByAppealResult(applicationId, appeal) {
  const application = findApplication(applicationId)
  if (!application || appeal?.reviewResult !== 'approved') return application || null
  const hours = Number(appeal.reviewHours)
  if (!Number.isFinite(hours) || hours < 0) return null
  const confirmedAt = nowText()
  application.recognizedHours = hours
  application.finalHours = hours
  application.approvedHours = hours
  application.finalStatus = 'approved'
  application.status = APPLICATION_STATUS.FINAL_APPROVED
  application.stage = APPLICATION_STAGE.FINISHED
  application.appealAdjusted = true
  application.appealId = appeal.appealId
  application.appealFinalConfirmTime = confirmedAt
  application.timelineEvents = [...(application.timelineEvents || []), {
    type: 'appeal_final_confirmed',
    title: `管理员最终确认申诉复审通过，课时结果已更新为 ${hours} 课时。`,
    time: confirmedAt,
  }]
  return application
}

export function getAdvisorPendingApplications(advisorId = '') {
  return applications.filter((application) => application.status === APPLICATION_STATUS.PENDING_ADVISOR
    && (!advisorId || application.mainAdvisor?.id === advisorId))
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
