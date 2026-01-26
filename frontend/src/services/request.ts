import Taro from '@tarojs/taro'
import { API_BASE_URL } from './config'
import { getToken, clearAuth } from '../utils/storage'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  header?: Record<string, string>
}

interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  user?: any
  token?: string
}

// 统一请求封装
export const request = async <T = any>(options: RequestOptions): Promise<ApiResponse<T>> => {
  const token = getToken()

  const header: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.header,
  }

  if (token) {
    header['Authorization'] = `Bearer ${token}`
  }

  try {
    const response = await Taro.request({
      url: `${API_BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header,
    })

    const result = response.data as ApiResponse<T>

    // Token 过期处理
    if (response.statusCode === 401) {
      clearAuth()
      Taro.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
      setTimeout(() => {
        Taro.redirectTo({ url: '/pages/login/index' })
      }, 1500)
      return { success: false, message: '登录已过期' }
    }

    return result
  } catch (error) {
    console.error('请求失败:', error)
    Taro.showToast({ title: '网络错误，请稍后重试', icon: 'none' })
    return { success: false, message: '网络错误' }
  }
}

// 便捷方法
export const get = <T = any>(url: string, data?: any) =>
  request<T>({ url, method: 'GET', data })

export const post = <T = any>(url: string, data?: any) =>
  request<T>({ url, method: 'POST', data })
