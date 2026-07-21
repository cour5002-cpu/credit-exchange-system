import { APPLICATION_STATUS, getApplications } from './applications.js'

export const EXCHANGE_STATUS = Object.freeze({
  PENDING_CONFIRMATION: 'pending_confirmation',
  PENDING_FINAL_CONFIRM: 'pending_final_confirm',
  PENDING_DISTRIBUTION_CONFIRM: 'pending_distribution_confirm',
  FINAL_APPROVED: 'final_approved',
  FINAL_REJECTED: 'final_rejected',
  COMPLETED: 'completed',
  REJECTED: 'rejected',
})

const exchanges = []
const FINAL_PENDING_STATUSES = [
  EXCHANGE_STATUS.PENDING_CONFIRMATION,
  EXCHANGE_STATUS.PENDING_FINAL_CONFIRM,
]
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

function getFinalApproveFailure(exchange) {
  if (!exchange) return '兑换申请不存在'
  if (!FINAL_PENDING_STATUSES.includes(exchange.status)) return '当前状态不可最终确认'
  if (!exchange.hoursArrived) return '课时尚未到账'
  if (exchange.exchanged) return '该申请已完成兑换'
  if (!isAdvisorConfirmed(exchange.advisorConfirmStatus)) return '指导老师确认状态无效'
  if (!exchange.memberDistributions?.length) return '成员学时 / 学分分配表不存在'
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
    teamName: '',
    taskName: '',
    source: '',
    sourceText: '',
    hoursArrived: true,
    exchanged: false,
    advisorConfirmStatus: 'approved',
    advisorComment: '',
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

export function getExchangeFinalConfirmList() {
  return exchanges.filter((exchange) => FINAL_PENDING_STATUSES.includes(exchange.status))
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

// 保留第四周早期 Mock 方法，供已有演示代码兼容使用。
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
