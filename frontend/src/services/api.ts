import { post, get } from './request'

// 用户认证
export const login = (phone: string, password: string) =>
  post('/api/login', { phone, password })

export const register = (phone: string, password: string, nickname?: string) =>
  post('/api/register', { phone, password, nickname })

export const logout = () =>
  post('/api/logout')

export const getUserProfile = () =>
  get('/api/user/profile')

// 伴侣绑定
export const generateBindingCode = () =>
  post('/api/bindcode/generate')

export const bindPartner = (code: string) =>
  post('/api/bind', { code })

export const unbindPartner = () =>
  post('/api/unbind')

// AI 教练
export const sendCoachMessage = (message: string) =>
  post('/api/coach/chat', { message })

export const getCoachHistory = () =>
  get('/api/coach/history')

export const clearCoachHistory = () =>
  post('/api/coach/clear')

// 情感客厅
export const sendLoungeMessage = (message: string, nickname: string) =>
  post('/api/lounge/send', { message, nickname })

export const getLoungeMessages = (lastId?: number) =>
  get('/api/lounge/messages', { last_id: lastId })
