export const EXCHANGE_STATUS = Object.freeze({
  PENDING_CONFIRMATION: 'pending_confirmation',
  PENDING_DISTRIBUTION_CONFIRM: 'pending_distribution_confirm',
  COMPLETED: 'completed',
  REJECTED: 'rejected',
})

const exchanges = []

function nowText() {
  const date = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function findExchange(id) {
  return exchanges.find((exchange) => exchange.id === id || exchange.exchangeId === id)
}

export function getExchanges() {
  return exchanges
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
    source: '',
    sourceText: '',
    finalHours: 0,
    exchangeHours: 0,
    estimatedCredits: 0,
    creditRule: { hoursPerCredit: 8, text: '每 8 课时兑换 1 学分' },
    proofMaterials: [],
    applyReason: '',
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
  const result = {
    total: uniqueIds.length,
    success: 0,
    failed: 0,
    failedItems: [],
  }

  uniqueIds.forEach((id) => {
    const exchange = findExchange(id)
    if (!exchange) {
      result.failed += 1
      result.failedItems.push({ id, reason: '兑换申请不存在' })
      return
    }
    if (exchange.status !== EXCHANGE_STATUS.PENDING_CONFIRMATION) {
      result.failed += 1
      result.failedItems.push({ id, reason: '当前状态不可确认' })
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
  exchange.distributionConfirmComment = comment
  exchange.distributionConfirmTime = nowText()
  return exchange
}
