import request from './request'

export function login(data) {
  return request.post('/api/auth/login', data)
}

export function getUserInfo() {
  return request.get('/api/auth/userinfo')
}

export function changePassword(data) {
  return request.post('/api/auth/change-password', data)
}

export function logout() {
  return request.post('/api/auth/logout')
}
