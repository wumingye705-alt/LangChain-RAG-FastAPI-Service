import { defineStore } from 'pinia'
import axios from 'axios'
import { apiConfig } from '../config/api'

const authHeaders = () => {
  const token = localStorage.getItem('jwt_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const normalizeSession = (session) => ({
  session_id: session.session_id || session.id,
  id: session.id || session.session_id,
  title: session.title || '未命名会话',
  created_at: session.created_at,
  updated_at: session.updated_at,
  history: session.history || [],
})

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessions: [],
    currentSession: null,
    loading: false,
  }),

  actions: {
    async getUserSessions(userId) {
      if (!userId) return { success: false, message: '缺少用户 ID' }
      this.loading = true
      try {
        const response = await axios.get(`${apiConfig.endpoints.getUserSessions}/${userId}`, {
          headers: authHeaders(),
        })
        const sessions = response.data.data?.sessions || []
        this.sessions = sessions.map(normalizeSession).sort((a, b) => {
          return new Date(b.updated_at || b.created_at || 0) - new Date(a.updated_at || a.created_at || 0)
        })
        return { success: true, data: this.sessions }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '获取会话失败' }
      } finally {
        this.loading = false
      }
    },

    async getSession(sessionId) {
      this.loading = true
      try {
        const response = await axios.get(`${apiConfig.endpoints.getSession}${sessionId}`, {
          headers: authHeaders(),
        })
        this.currentSession = normalizeSession(response.data.data || response.data)
        return { success: true, data: this.currentSession }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '获取会话详情失败' }
      } finally {
        this.loading = false
      }
    },

    async deleteSession(sessionId) {
      this.loading = true
      try {
        await axios.delete(`${apiConfig.endpoints.deleteSession}${sessionId}`, {
          headers: authHeaders(),
        })
        this.sessions = this.sessions.filter((session) => session.session_id !== sessionId)
        if (this.currentSession?.session_id === sessionId) this.currentSession = null
        return { success: true, message: '会话已删除' }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '删除会话失败' }
      } finally {
        this.loading = false
      }
    },

    setCurrentSession(session) {
      this.currentSession = session ? normalizeSession(session) : null
    },

    clearSessions() {
      this.sessions = []
      this.currentSession = null
    },
  },
})
