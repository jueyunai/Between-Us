// API 配置
export const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:8080'
  : 'https://between-us.zeabur.app'
