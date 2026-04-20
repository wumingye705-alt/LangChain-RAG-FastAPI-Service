import { defineStore } from 'pinia'
import axios from 'axios'
import { apiConfig } from '../config/api'

const tokenKey = 'jwt_token'

const authHeaders = () => {
  const token = localStorage.getItem(tokenKey)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const pickError = (error, fallback) => {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (typeof data.message === 'string') return data.message
  if (data.detail && typeof data.detail === 'object') {
    const first = Object.values(data.detail)[0]
    return Array.isArray(first) ? first[0] : String(first)
  }
  return fallback
}

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    token: localStorage.getItem(tokenKey) || '',
  }),

  getters: {
    isLogin: (state) => Boolean(state.token),
    getLoginStatus: (state) => Boolean(state.token),
    getToken: (state) => state.token,
    getUserInfo: (state) => state.userInfo,
  },

  actions: {
    setSession(token, user) {
      this.token = token || ''
      this.userInfo = user || null
      if (token) localStorage.setItem(tokenKey, token)
      else localStorage.removeItem(tokenKey)
    },

    async login({ username, password }) {
      try {
        const response = await axios.post(apiConfig.endpoints.login, { username, password })
        this.setSession(response.data.token, response.data.user)
        return { success: true, message: response.data.message || '登录成功' }
      } catch (error) {
        return { success: false, message: pickError(error, '登录失败') }
      }
    },

    async register(form) {
      try {
        const response = await axios.post(apiConfig.endpoints.register, {
          username: form.username,
          email: form.email,
          telephone: form.telephone || '',
          password: form.password,
          confirm_password: form.confirm_password,
        })
        this.setSession(response.data.token, response.data.user)
        return { success: true, message: response.data.message || '注册成功' }
      } catch (error) {
        return { success: false, message: pickError(error, '注册失败') }
      }
    },

    async getUserInfoDetail() {
      if (!this.token) return { success: false, message: '请先登录' }
      try {
        const response = await axios.get(apiConfig.endpoints.profile, { headers: authHeaders() })
        this.userInfo = response.data.data || response.data.user || response.data
        return { success: true, data: this.userInfo, message: response.data.message || '已更新资料' }
      } catch (error) {
        return { success: false, message: pickError(error, '获取用户信息失败') }
      }
    },

    async updateUserInfo(userData) {
      if (!this.token) return { success: false, message: '请先登录' }
      try {
        const response = await axios.put('/user/update/', userData, {
          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        })
        if (response.data.token) this.setSession(response.data.token, response.data.user)
        else this.userInfo = response.data.user || this.userInfo
        return { success: true, message: response.data.message || '资料已保存' }
      } catch (error) {
        return { success: false, message: pickError(error, '更新资料失败') }
      }
    },

    async updatePassword(oldPassword, newPassword) {
      if (!this.token) return { success: false, message: '请先登录' }
      try {
        const response = await axios.post('/user/reset-password/', {
          old_password: oldPassword,
          new_password: newPassword,
          confirm_password: newPassword,
        }, { headers: authHeaders() })
        if (response.data.token) this.setSession(response.data.token, this.userInfo)
        return { success: true, message: response.data.message || '密码已更新' }
      } catch (error) {
        return { success: false, message: pickError(error, '更新密码失败') }
      }
    },

    async logout() {
      try {
        if (this.token) await axios.post(apiConfig.endpoints.logout, {}, { headers: authHeaders() })
      } finally {
        this.setSession('', null)
      }
    },
  },

  persist: true,
})
