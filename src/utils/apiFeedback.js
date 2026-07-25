export function getApiErrorMessage(error, fallback = '操作失败，请稍后重试') {
  if (error?.code === 40901 || error?.status === 409 || error?.category === 'conflict') {
    return '当前状态已变化，请刷新后重试'
  }
  if (error?.code === 40101 || error?.status === 401) return '登录状态已失效，请重新登录'
  if (error?.code === 40301 || error?.status === 403) return '当前账号无权执行此操作'
  return error?.message || fallback
}

export function hasServerAction(actions, names, fallback = false) {
  const keys = Array.isArray(names) ? names : [names]
  if (Array.isArray(actions)) return keys.some((key) => actions.includes(key))
  if (actions && typeof actions === 'object' && Object.keys(actions).length) {
    return keys.some((key) => actions[key] === true || actions[key]?.allowed === true)
  }
  return fallback
}
