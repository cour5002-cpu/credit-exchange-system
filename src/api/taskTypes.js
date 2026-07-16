const TASK_TYPE_LIST_ENDPOINT = '/api/v1/task-types'
const ADMIN_TASK_TYPE_ENDPOINT = '/api/v1/admin/task-types'

// 以下方法仅返回请求配置，当前页面使用前端 Mock 数据，不会调用后端。
export function getTaskTypesRequest() {
  return { url: TASK_TYPE_LIST_ENDPOINT, options: { method: 'GET' } }
}

export function createTaskTypeRequest(data) {
  return {
    url: ADMIN_TASK_TYPE_ENDPOINT,
    options: { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) },
  }
}

export function updateTaskTypeRequest(id, data) {
  return {
    url: `${ADMIN_TASK_TYPE_ENDPOINT}/${id}`,
    options: { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) },
  }
}

export function enableTaskTypeRequest(id) {
  return { url: `${ADMIN_TASK_TYPE_ENDPOINT}/${id}/enable`, options: { method: 'POST' } }
}

export function disableTaskTypeRequest(id) {
  return { url: `${ADMIN_TASK_TYPE_ENDPOINT}/${id}/disable`, options: { method: 'POST' } }
}
