import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken, removeUserInfo } from '../utils/storage'
import router from '../router'

const request = axios.create({
  timeout: 10000
})

request.interceptors.request.use(config => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const status = error.response?.status
    const msg = error.response?.data?.msg || '请求失败'
    if (status === 401) {
      removeToken()
      removeUserInfo()
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default request
