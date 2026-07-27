import { reactive } from 'vue'
import { getSystemTime } from '../api/systemApi.js'

export const systemTimeState = reactive({
  serverTime: '',
  offsetMs: 0,
  initialized: false,
})

export async function initializeSystemTime() {
  try {
    const payload = await getSystemTime()
    const serverTime = payload?.server_time ?? payload?.serverTime
    const serverMs = Date.parse(serverTime)
    if (!Number.isFinite(serverMs)) throw new Error('服务器时间格式无效')
    systemTimeState.serverTime = serverTime
    systemTimeState.offsetMs = serverMs - Date.now()
    systemTimeState.initialized = true
  } catch (error) {
    systemTimeState.initialized = false
    console.warn('[system-time] 系统时间校准失败，将不使用浏览器时间判断业务状态。', error)
  }
  return systemTimeState
}

export const getServerNowMs = () => Date.now() + systemTimeState.offsetMs
