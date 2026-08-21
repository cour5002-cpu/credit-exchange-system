const STATUS_TEXT = Object.freeze({ enabled: '已启用', disabled: '已停用' })

const adaptRuleTaskType = (item) => item ? ({
  ...item,
  id: item.id,
  name: item.type_name ?? item.name,
  code: item.type_code ?? item.code,
}) : null

export function adaptExtensionRule(item) {
  if (!item) return null
  return {
    id: item.id,
    ruleName: item.rule_name,
    ordinaryMaxDays: item.ordinary_max_days,
    specialThresholdDays: item.special_threshold_days,
    specialMaxDays: item.special_max_days,
    maxExtensionRequests: item.max_extension_requests,
    defaultMaterialDueDays: item.default_material_due_days,
    allowBeyondGraduation: item.allow_beyond_graduation,
    taskTypes: (Array.isArray(item.task_types) ? item.task_types : []).map(adaptRuleTaskType).filter(Boolean),
    effectiveAt: item.effective_at,
    status: item.status,
    statusText: STATUS_TEXT[item.status] ?? item.status ?? '--',
    version: item.version,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  }
}

export const adaptExtensionRuleEnvelope = (payload) => adaptExtensionRule(payload?.extension_rule ?? payload?.rule ?? payload)

export function adaptCurrentExtensionRule(payload) {
  if (payload && Object.prototype.hasOwnProperty.call(payload, 'rule')) {
    return { rule: payload.rule === null ? null : adaptExtensionRule(payload.rule) }
  }
  return { rule: adaptExtensionRuleEnvelope(payload) }
}

export const adaptExtensionRuleList = (payload) => ({
  ...(payload ?? {}),
  items: (Array.isArray(payload) ? payload : payload?.items ?? []).map(adaptExtensionRule).filter(Boolean),
})
