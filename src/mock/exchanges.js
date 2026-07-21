const exchanges = []

function nowText() {
  const date = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
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
    ...exchange,
    exchangeId,
    id: exchangeId,
    estimatedCredits: exchange.estimatedCredits ?? exchange.expectedCredits ?? 0,
    proofMaterials: exchange.proofMaterials ?? (exchange.attachment ? [exchange.attachment] : []),
    applyReason: exchange.applyReason ?? exchange.description ?? '',
    submitTime: exchange.submitTime || nowText(),
    status: exchange.status || 'pending_confirmation',
  }
  exchanges.push(addedExchange)
  return addedExchange
}
