const TOKEN_KEY = 'token'
const USER_KEY = 'user_info'
const REMEMBER_KEY = 'remember_info'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getUserInfo() {
  const raw = localStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) : null
}

export function setUserInfo(info) {
  localStorage.setItem(USER_KEY, JSON.stringify(info))
}

export function removeUserInfo() {
  localStorage.removeItem(USER_KEY)
}

export function getRememberInfo() {
  const raw = localStorage.getItem(REMEMBER_KEY)
  if (!raw) return null
  try {
    const data = JSON.parse(raw)
    if (data.expire && Date.now() > data.expire) {
      removeRememberInfo()
      return null
    }
    return data
  } catch {
    return null
  }
}

export function setRememberInfo(username, password) {
  const data = {
    username,
    password: btoa(password),
    expire: Date.now() + 7 * 24 * 3600 * 1000
  }
  localStorage.setItem(REMEMBER_KEY, JSON.stringify(data))
}

export function removeRememberInfo() {
  localStorage.removeItem(REMEMBER_KEY)
}
