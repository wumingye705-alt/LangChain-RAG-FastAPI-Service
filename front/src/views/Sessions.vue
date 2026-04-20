<template>
  <div class="app-shell">
    <TabBar />
    <main class="page">
      <header class="topbar">
        <div>
          <h2>会话管理</h2>
          <p>继续旧问题，或者清理不需要的记录。</p>
        </div>
        <button class="btn primary" @click="router.push('/aichat')">开始新会话</button>
      </header>

      <section class="sessions-grid">
        <article v-if="!userStore.getLoginStatus" class="panel empty-state">
          登录后可以查看属于你的会话。
          <button class="btn primary" @click="router.push('/login')">去登录</button>
        </article>

        <article v-else-if="loading" class="panel empty-state">正在读取会话...</article>

        <article v-else-if="sessions.length === 0" class="panel empty-state">
          还没有会话。发出第一个问题后，这里会出现记录。
        </article>

        <article v-for="session in sessions" v-else :key="session.session_id" class="session-card panel">
          <div>
            <span>{{ formatDate(session.updated_at || session.created_at) }}</span>
            <h3>{{ session.title || '未命名会话' }}</h3>
            <p>{{ session.session_id }}</p>
          </div>
          <div class="card-actions">
            <button class="btn primary" @click="openSession(session)">打开</button>
            <button class="btn danger" @click="removeSession(session.session_id)">删除</button>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import TabBar from '../components/TabBar.vue'
import { useUserStore } from '../store/user'
import { useSessionStore } from '../store/session'

const router = useRouter()
const userStore = useUserStore()
const sessionStore = useSessionStore()
const loading = ref(false)
const sessions = computed(() => sessionStore.sessions)

const load = async () => {
  if (!userStore.getLoginStatus) return
  if (!userStore.userInfo) await userStore.getUserInfoDetail()
  const userId = userStore.userInfo?.id || userStore.userInfo?.uuid
  if (!userId) return
  loading.value = true
  const result = await sessionStore.getUserSessions(userId)
  loading.value = false
  if (!result.success) showToast(result.message)
}

const openSession = (session) => {
  router.push(`/aichat/${session.session_id}`)
}

const removeSession = async (id) => {
  const result = await sessionStore.deleteSession(id)
  showToast(result.message)
}

const formatDate = (value) => {
  if (!value) return '暂无时间'
  return new Date(value).toLocaleString()
}

onMounted(load)
</script>

<style scoped>
.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.session-card {
  padding: 18px;
  display: grid;
  gap: 18px;
}

.session-card span {
  color: var(--accent);
  font-size: 13px;
  font-weight: 800;
}

.session-card h3 {
  margin: 8px 0;
  font-size: 18px;
}

.session-card p {
  margin: 0;
  color: var(--muted);
  word-break: break-all;
}

.card-actions {
  display: flex;
  gap: 8px;
}
</style>
