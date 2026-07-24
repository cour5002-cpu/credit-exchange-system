import { getAdvisors, getReviewers, getTaskTypes } from '../api/taskApi.js'
import { adaptAdvisor, adaptReviewer, adaptTaskType, getListItems } from '../adapters/commonAdapter.js'

async function loadWithFallback(request, adapter, fallback, label) {
  try {
    const items = getListItems(await request()).map(adapter).filter(Boolean)
    if (items.length) return items
    throw new Error(`${label}接口返回空列表`)
  } catch (error) {
    console.warn(`[common-api] ${label}加载失败，继续使用 Mock 回退。`, error)
    return fallback.map((item) => ({ ...item }))
  }
}

export const loadTaskTypeOptions = (fallback = []) =>
  loadWithFallback(() => getTaskTypes({ enabled: true }), adaptTaskType, fallback, '任务类别')

export const loadAdvisorOptions = (fallback = []) =>
  loadWithFallback(() => getAdvisors(), adaptAdvisor, fallback, '指导老师')

export const loadReviewerOptions = (fallback = []) =>
  loadWithFallback(() => getReviewers(), adaptReviewer, fallback, '审核老师')
