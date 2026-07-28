import { getAdvisors, getReviewers, getTaskTypes } from '../api/taskApi.js'
import { adaptAdvisor, adaptReviewer, adaptTaskType, getListItems } from '../adapters/commonAdapter.js'

async function loadOptions(request, adapter) {
  return getListItems(await request()).map(adapter).filter(Boolean)
}

export const loadTaskTypeOptions = () =>
  loadOptions(() => getTaskTypes({ enabled: true }), adaptTaskType)

export const loadAdvisorOptions = () =>
  loadOptions(() => getAdvisors(), adaptAdvisor)

export const loadReviewerOptions = () =>
  loadOptions(() => getReviewers(), adaptReviewer)
