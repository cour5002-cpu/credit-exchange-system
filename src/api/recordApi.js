import { get } from './request.js'

export const getOperationRecords = (params) => get('/operation-records', params)
export const getOperationRecord = (id) => get(`/operation-records/${id}`)

