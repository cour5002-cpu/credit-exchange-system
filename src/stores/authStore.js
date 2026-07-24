import { computed, reactive, readonly } from 'vue'
import * as authApi from '../api/authApi.js'
import { adaptCurrentUser } from '../adapters/userAdapter.js'

const state = reactive({
  user: null,
  initialized: false,
  restoring: false,
})

let restorePromise = null

export function getPortalRole(user = state.user) {
  if (!user) return null
  // 联调临时规则：同为教师账号时按用户名确定默认端，后续替换为角色选择页。
  if (user.username === 'teacher1') return 'advisor'
  if (user.username === 'teacher2') return 'reviewer'
  if (['student', 'advisor', 'reviewer', 'admin'].includes(user.role)) return user.role
  return null
}

export function getHomePath(user = state.user) {
  return {
    student: '/student/dashboard',
    advisor: '/teacher/dashboard',
    reviewer: '/reviewer/dashboard',
    admin: '/admin/dashboard',
  }[getPortalRole(user)] || '/login'
}

function saveUser(payload, fallbackUsername = '') {
  const source = payload?.user || payload
  const user = adaptCurrentUser(source)
  if (user && !user.username) user.username = fallbackUsername
  state.user = user
  state.initialized = true
  return user
}

export async function login(credentials) {
  await authApi.login(credentials)
  const payload = await authApi.getMe()
  return saveUser(payload, credentials.username)
}

export async function restoreSession({ force = false } = {}) {
  if (state.initialized && !force) return state.user
  if (restorePromise) return restorePromise
  state.restoring = true
  restorePromise = authApi.getMe()
    .then((payload) => saveUser(payload))
    .catch((error) => {
      state.user = null
      state.initialized = true
      if (error?.code === 40101 || error?.status === 401 || error?.category === 'unauthorized') return null
      throw error
    })
    .finally(() => {
      state.restoring = false
      restorePromise = null
    })
  return restorePromise
}

export async function logout() {
  try {
    await authApi.logout()
  } finally {
    state.user = null
    state.initialized = true
  }
}

export const authState = readonly(state)
export const currentUser = computed(() => state.user)
export const isAuthenticated = computed(() => Boolean(state.user))

