import { get, post } from './request.js'

export const login = (credentials) => post('/auth/login', credentials)
export const logout = () => post('/auth/logout')
export const getCurrentUser = () => get('/me')

