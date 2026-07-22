import { APPLICATION_STATUS, getApplications } from './applications.js'

export const EXCHANGE_STATUS = Object.freeze({
  PENDING_CONFIRMATION: 'pending_confirmation',
  PENDING_FINAL_CONFIRM: 'pending_final_confirm',
  PENDING_DISTRIBUTION_CONFIRM: 'pending_distribution_confirm',
  FINAL_APPROVED: 'final_approved',
  FINAL_REJECTED: 'final_rejected',
  COMPLETED: 'completed',
  ADVISOR_REJECTED: 'advisor_rejected',
  REJECTED: 'rejected',
})

export const PENDING_CREDIT_STATUSES = Object.freeze([
  EXCHANGE_STATUS.PENDING_CONFIRMATION,
  EXCHANGE_STATUS.PENDING_FINAL_CONFIRM,
  EXCHANGE_STATUS.PENDING_DISTRIBUTION_CONFIRM,
])

const exchanges = []
const FINAL_PENDING_STATUSES = [EXCHANGE_STATUS.PENDING_FINAL_CONFIRM]
const ACTIVE_EXCHANGE_STATUSES = [
  EXCHANGE_STATUS.PENDING_CONFIRMATION,
  EXCHANGE_STATUS.PENDING_FINAL_CONFIRM,
  EXCHANGE_STATUS.PENDING_DISTRIBUTION_CONFIRM,
  EXCHANGE_STATUS.FINAL_APPROVED,
  EXCHANGE_STATUS.COMPLETED,
]

function nowText() {
  const date = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function findExchange(id) {
  return exchanges.find((exchange) => exchange.id === id || exchange.exchangeId === id)
}

function isAdvisorConfirmed(status) {
  return ['approved', 'confirmed'].includes(status)
}

function sumMemberValue(exchange, field) {
  return (exchange?.memberDistributions || []).reduce((sum, member) => sum + Number(member[field] || 0), 0)
}

function getFinalApproveFailure(exchange) {
  if (!exchange) return '兑换申请不存在'
  if (!FINAL_PENDING_STATUSES.includes(exchange.status)) return '当前状态不可最终确认'
  if (!exchange.hoursArrived) return '课时尚未到账'
  if (exchange.exchanged) return '该申请已完成兑换'
  if (!isAdvisorConfirmed(exchange.advisorConfirmStatus)) return '指导老师确认状态无效'
  if (!exchange.memberDistributions?.length) return '成员学时 / 学分分配表不存在'
  const allocatedHours = sumMemberValue(exchange, 'allocatedHours')
  if (Math.abs(allocatedHours - Number(exchange.finalHours || 0)) > 0.000001) {
    return '成员分配课时总和与项目最终认定课时不一致，请驳回后由学生重新提交。'
  }
  if (exchange.memberDistributions.some((member) => Number(member.allocatedHours) < 0)) return '成员分配课时不能小于 0'
  const allocatedCredits = sumMemberValue(exchange, 'allocatedCredits')
  const creditTolerance = Math.max(0.01, exchange.memberDistributions.length * 0.005)
  if (Math.abs(allocatedCredits - Number(exchange.estimatedCredits || 0)) > creditTolerance + 0.000001) {
    return '成员分配学分总和与项目预计总学分不一致'
  }
  return ''
}

function createBatchResult(ids) {
  return { total: ids.length, success: 0, failed: 0, failedItems: [] }
}

export function getExchanges() {
  return exchanges
}

export function isHoursArrived(application) {
  if (!application) return false
  if (application.hoursArrived !== undefined) return Boolean(application.hoursArrived)
  if (application.hoursPosted !== undefined) return Boolean(application.hoursPosted)
  if (application.arrived !== undefined) return Boolean(application.arrived)
  return application.status === APPLICATION_STATUS.FINAL_APPROVED
}

export function hasActiveExchange(applicationId) {
  if (!applicationId) return false
  return exchanges.some((exchange) =>
    exchange.applicationId === applicationId
    && ACTIVE_EXCHANGE_STATUSES.includes(exchange.status),
  )
}

export function getAvailableExchangeApplications(currentStudentId) {
  return getApplications().filter((application) =>
    application.captainId === currentStudentId
    && application.status === APPLICATION_STATUS.FINAL_APPROVED
    && isHoursArrived(application)
    && !hasActiveExchange(application.id),
  )
}

export function addExchange(exchange) {
  const exchangeId = exchange.exchangeId || exchange.id || `EX-${Date.now()}`
  const addedExchange = {
    exchangeId,
    id: exchangeId,
    applicationId: '',
    projectTitle: '',
    studentName: '',
    studentId: '',
    captainId: '',
    captainName: '',
    teamName: '',
    taskName: '',
    source: '',
    sourceText: '',
    hoursArrived: false,
    exchanged: false,
    advisorId: '',
    advisorName: '',
    advisorConfirmStatus: EXCHANGE_STATUS.PENDING_CONFIRMATION,
    advisorComment: '',
    advisorConfirmTime: '',
    finalHours: 0,
    exchangeHours: 0,
    estimatedCredits: 0,
    creditRule: { hoursPerCredit: 8, text: '每 8 课时兑换 1 学分' },
    memberDistributions: [],
    proofMaterials: [],
    applyReason: '',
    finalStatus: 'pending',
    finalComment: '',
    finalConfirmTime: '',
    confirmationComment: '',
    confirmationTime: '',
    distributionConfirmComment: '',
    distributionConfirmTime: '',
    ...exchange,
    exchangeId,
    id: exchangeId,
    estimatedCredits: exchange.estimatedCredits ?? exchange.expectedCredits ?? 0,
    memberDistributions: (exchange.memberDistributions || []).map((member) => ({
      studentName: member.studentName ?? member.name ?? '',
      studentId: member.studentId ?? '',
      role: member.role ?? (member.isCaptain ? 'captain' : 'member'),
      allocatedHours: Number(member.allocatedHours || 0),
      allocatedCredits: Number((Number(member.allocatedHours || 0) / 8).toFixed(2)),
      remark: member.remark ?? member.description ?? '',
    })),
    proofMaterials: exchange.proofMaterials ?? (exchange.attachment ? [exchange.attachment] : []),
    applyReason: exchange.applyReason ?? exchange.description ?? '',
    submitTime: exchange.submitTime || nowText(),
    status: exchange.status || EXCHANGE_STATUS.PENDING_CONFIRMATION,
  }
  exchanges.push(addedExchange)
  return addedExchange
}

export function getPendingConfirmationExchanges() {
  return exchanges.filter((exchange) => exchange.status === EXCHANGE_STATUS.PENDING_CONFIRMATION)
}

export function getAdvisorPendingExchanges(advisorId) {
  return exchanges.filter((exchange) =>
    exchange.status === EXCHANGE_STATUS.PENDING_CONFIRMATION
    && (!advisorId || exchange.advisorId === advisorId),
  )
}

export function getAdvisorProcessedExchanges(advisorId) {
  return exchanges.filter((exchange) =>
    exchange.advisorConfirmTime
    && (!advisorId || exchange.advisorId === advisorId),
  )
}

export function advisorApproveExchange(id, comment = '') {
  const exchange = findExchange(id)
  if (!exchange || exchange.status !== EXCHANGE_STATUS.PENDING_CONFIRMATION) return null
  if (!exchange.memberDistributions?.length) return null
  if (Math.abs(sumMemberValue(exchange, 'allocatedHours') - Number(exchange.finalHours || 0)) > 0.000001) return null
  exchange.status = EXCHANGE_STATUS.PENDING_FINAL_CONFIRM
  exchange.advisorConfirmStatus = 'approved'
  exchange.advisorComment = comment.trim()
  exchange.advisorConfirmTime = nowText()
  return exchange
}

export function advisorRejectExchange(id, comment) {
  const exchange = findExchange(id)
  if (!exchange || exchange.status !== EXCHANGE_STATUS.PENDING_CONFIRMATION || !comment?.trim()) return null
  exchange.status = EXCHANGE_STATUS.ADVISOR_REJECTED
  exchange.advisorConfirmStatus = 'rejected'
  exchange.advisorComment = comment.trim()
  exchange.advisorConfirmTime = nowText()
  return exchange
}

export function getExchangeFinalConfirmList() {
  return exchanges.filter((exchange) => FINAL_PENDING_STATUSES.includes(exchange.status))
}

export function getExchangeFinalApproveFailure(exchange) {
  return getFinalApproveFailure(exchange)
}

export function finalApproveExchange(id, comment = '') {
  const exchange = findExchange(id)
  if (getFinalApproveFailure(exchange)) return null
  exchange.status = EXCHANGE_STATUS.FINAL_APPROVED
  exchange.finalStatus = 'approved'
  exchange.finalComment = comment
  exchange.finalConfirmTime = nowText()
  exchange.exchanged = true
  return exchange
}

export function finalRejectExchange(id, comment) {
  const exchange = findExchange(id)
  if (!exchange || !FINAL_PENDING_STATUSES.includes(exchange.status) || !comment?.trim()) return null
  exchange.status = EXCHANGE_STATUS.FINAL_REJECTED
  exchange.finalStatus = 'rejected'
  exchange.finalComment = comment.trim()
  exchange.finalConfirmTime = nowText()
  return exchange
}

export function batchFinalApproveExchanges(ids, comment = '') {
  const uniqueIds = [...new Set(ids)]
  const result = createBatchResult(uniqueIds)
  uniqueIds.forEach((id) => {
    const exchange = findExchange(id)
    const reason = getFinalApproveFailure(exchange)
    if (reason) {
      result.failed += 1
      result.failedItems.push({ id, reason })
      return
    }
    finalApproveExchange(id, comment)
    result.success += 1
  })
  return result
}

export function batchFinalRejectExchanges(ids, comment) {
  const uniqueIds = [...new Set(ids)]
  const result = createBatchResult(uniqueIds)
  uniqueIds.forEach((id) => {
    const exchange = findExchange(id)
    let reason = ''
    if (!comment?.trim()) reason = '批量驳回必须填写处理意见'
    else if (!exchange) reason = '兑换申请不存在'
    else if (!FINAL_PENDING_STATUSES.includes(exchange.status)) reason = '当前状态不可驳回'
    if (reason) {
      result.failed += 1
      result.failedItems.push({ id, reason })
      return
    }
    finalRejectExchange(id, comment)
    result.success += 1
  })
  return result
}

// 旧兼容方法，不建议新流程继续调用。保留供已有演示代码兼容使用。
export function approveExchange(id, comment = '') {
  const exchange = findExchange(id)
  if (!exchange || exchange.status !== EXCHANGE_STATUS.PENDING_CONFIRMATION) return null
  exchange.status = EXCHANGE_STATUS.PENDING_DISTRIBUTION_CONFIRM
  exchange.confirmationComment = comment
  exchange.confirmationTime = nowText()
  return exchange
}

export function batchApproveExchanges(ids, comment = '') {
  const uniqueIds = [...new Set(ids)]
  const result = createBatchResult(uniqueIds)
  uniqueIds.forEach((id) => {
    const exchange = findExchange(id)
    if (!exchange || exchange.status !== EXCHANGE_STATUS.PENDING_CONFIRMATION) {
      result.failed += 1
      result.failedItems.push({ id, reason: exchange ? '当前状态不可确认' : '兑换申请不存在' })
      return
    }
    approveExchange(id, comment)
    result.success += 1
  })
  return result
}

export function getPendingDistributionConfirmExchanges() {
  return exchanges.filter((exchange) => exchange.status === EXCHANGE_STATUS.PENDING_DISTRIBUTION_CONFIRM)
}

export function completeExchange(id, comment = '') {
  const exchange = findExchange(id)
  if (!exchange || exchange.status !== EXCHANGE_STATUS.PENDING_DISTRIBUTION_CONFIRM) return null
  exchange.status = EXCHANGE_STATUS.COMPLETED
  exchange.finalStatus = 'approved'
  exchange.exchanged = true
  exchange.distributionConfirmComment = comment
  exchange.distributionConfirmTime = nowText()
  return exchange
}
