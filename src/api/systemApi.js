import { get } from './request.js'

export const getSystemTime = () => get('/system/time')
