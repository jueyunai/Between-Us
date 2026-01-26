import Taro from '@tarojs/taro'

const TOKEN_KEY = 'auth_token'
const USER_KEY = 'user_info'

// Token 管理
export const getToken = (): string | null => {
  return Taro.getStorageSync(TOKEN_KEY) || null
}

export const setToken = (token: string): void => {
  Taro.setStorageSync(TOKEN_KEY, token)
}

export const removeToken = (): void => {
  Taro.removeStorageSync(TOKEN_KEY)
}

// 用户信息管理
export interface UserInfo {
  id: number
  phone: string
  nickname?: string
  binding_code?: string
  partner_id?: number
  has_partner: boolean
}

export const getUserInfo = (): UserInfo | null => {
  const info = Taro.getStorageSync(USER_KEY)
  return info ? JSON.parse(info) : null
}

export const setUserInfo = (user: UserInfo): void => {
  Taro.setStorageSync(USER_KEY, JSON.stringify(user))
}

export const removeUserInfo = (): void => {
  Taro.removeStorageSync(USER_KEY)
}

// 清除所有登录信息
export const clearAuth = (): void => {
  removeToken()
  removeUserInfo()
}
