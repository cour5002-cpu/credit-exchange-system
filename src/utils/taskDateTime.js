export function toShanghaiIso(value) {
  if (!value) return value
  const text = String(value).trim()
  if (/Z$|[+-]\d{2}:\d{2}$/.test(text)) return text
  const normalized = text.replace(' ', 'T')
  return `${normalized.length === 16 ? `${normalized}:00` : normalized}+08:00`
}

export function toShanghaiDateTimeInput(value) {
  if (!value) return ''
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return String(value).slice(0, 16)
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date).reduce((result, item) => ({ ...result, [item.type]: item.value }), {})
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`
}
