<template>
  <div class="app-shell">
    <TabBar />

    <main class="page chat-page">
      <section class="chat-main panel">
        <header class="chat-header">
          <div>
            <span class="eyebrow">RAG Assistant</span>
            <h2>今天想查什么？</h2>
            <p>支持流式回答、会话保存和知识库检索。</p>
          </div>
          <div class="header-actions">
            <button class="btn" @click="newChat">新会话</button>
            <button class="btn" @click="router.push('/sessions')">会话列表</button>
          </div>
        </header>

        <div ref="messagesEl" class="messages">
          <article
            v-for="message in messages"
            :key="message.id"
            :class="['message-row', message.role]"
          >
            <div class="avatar">{{ message.role === 'user' ? '你' : 'AI' }}</div>
            <div class="bubble">
              <div v-if="message.loading" class="typing">正在整理答案...</div>
              <div v-else class="markdown" v-html="renderMarkdown(message.content)" />
            </div>
          </article>
        </div>

        <form class="composer" @submit.prevent="sendMessage">
          <textarea
            v-model="input"
            class="field"
            rows="3"
            placeholder="输入问题，按 Ctrl + Enter 发送"
            @keydown.ctrl.enter.prevent="sendMessage"
          />
          <div class="composer-footer">
            <span>{{ statusText }}</span>
            <button class="btn primary" type="submit" :disabled="loading || !input.trim()">
              {{ loading ? '生成中' : '发送' }}
            </button>
          </div>
        </form>
      </section>

      <aside class="right-rail">
        <section class="panel knowledge-panel">
          <div class="rail-body">
            <div class="rail-title">
              <div>
                <h3>资料库</h3>
                <p>上传后会写入后端向量库，当前页面记录最近上传。</p>
              </div>
              <strong>{{ uploadedFiles.length }}</strong>
            </div>
            <input ref="fileInput" type="file" multiple class="hidden-input" @change="uploadFiles" />
            <button class="btn primary" :disabled="uploading" @click="fileInput?.click()">
              {{ uploading ? '上传中' : '上传资料' }}
            </button>
            <button class="btn danger" @click="cleanVectors">清空向量库</button>
            <div v-if="uploadedFiles.length" class="upload-list">
              <div v-for="file in uploadedFiles" :key="file.id" class="upload-item">
                <span>{{ file.name }}</span>
                <small>{{ file.size }} · {{ file.time }} · {{ file.indexed ? '已入库' : '处理中' }}</small>
                <button v-if="file.downloadUrl" class="file-link" type="button" @click="openUploadedFile(file)">
                  查看原文件
                </button>
              </div>
            </div>
            <div v-else class="upload-empty">
              还没有上传记录。支持 PDF、TXT、MD、PPTX、DOCX。
            </div>
          </div>
        </section>

        <section class="panel tips-panel">
          <h3>提问模板</h3>
          <button v-for="tip in tips" :key="tip" class="tip" @click="input = tip">{{ tip }}</button>
        </section>
      </aside>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { showToast } from 'vant'
import TabBar from '../components/TabBar.vue'
import { useUserStore } from '../store/user'
import { useSessionStore } from '../store/session'
import { apiConfig } from '../config/api'
import 'highlight.js/styles/github.css'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const sessionStore = useSessionStore()

const input = ref('')
const loading = ref(false)
const uploading = ref(false)
const sessionId = ref('')
const messagesEl = ref(null)
const fileInput = ref(null)
const uploadedFiles = ref([])
const messages = ref([
  {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: '你好，我可以帮你基于资料回答问题。先登录，再上传材料或直接提问。',
  },
])

const tips = [
  '请总结我上传资料中的核心观点。',
  '把这份材料整理成三条行动建议。',
  '找出文档里和风险、成本、时间有关的信息。',
]

const statusText = computed(() => {
  if (!userStore.getLoginStatus) return '未登录时无法保存会话'
  if (sessionId.value) return `会话 ${sessionId.value.slice(0, 8)}`
  return '准备开始新会话'
})

const renderMarkdown = (content) => {
  return DOMPurify.sanitize(marked.parse(content || '', { breaks: true, gfm: true }))
}

const friendlyError = (message) => {
  const text = String(message || '')
  if (text.includes('dashscope.aliyuncs.com') || text.includes('SSLEOFError') || text.includes('HTTPSConnectionPool')) {
    return '大模型服务连接中断了。请稍等几秒后重试；如果连续出现，请重启后端服务并检查网络或代理。'
  }
  if (text.includes('401') || text.includes('api key') || text.includes('API key')) {
    return '模型 API Key 可能无效，请检查 backend/.env 中的 ALIYUN_ACCESS_KEY_SECRET。'
  }
  return text || '请求失败，请检查后端服务。'
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

const formatSize = (size) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const authHeaders = () => {
  const token = localStorage.getItem('jwt_token') || userStore.token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const normalizeFileRecord = (file) => ({
  id: file.file_id || file.id || crypto.randomUUID(),
  name: file.filename || file.name || file.stored_filename || '未命名文件',
  size: formatSize(Number(file.size || 0)),
  time: file.uploaded_at ? new Date(file.uploaded_at).toLocaleString() : '',
  downloadUrl: file.download_url || file.downloadUrl || '',
  indexed: file.indexed !== false,
})

const loadUploadedFiles = async () => {
  if (!userStore.getLoginStatus) return
  try {
    const response = await fetch(apiConfig.endpoints.listVectorFiles, { headers: authHeaders() })
    if (!response.ok) throw new Error('获取资料列表失败')
    const result = await response.json()
    uploadedFiles.value = (result.data?.files || []).map(normalizeFileRecord)
  } catch (error) {
    console.warn(error)
  }
}

const openUploadedFile = async (file) => {
  if (!file.downloadUrl) return
  try {
    const response = await fetch(file.downloadUrl, { headers: authHeaders() })
    if (!response.ok) throw new Error('无法打开文件')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank', 'noopener')
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (error) {
    showToast(error.message || '无法打开文件')
  }
}

const ensureLogin = () => {
  if (userStore.getLoginStatus) return true
  showToast('请先登录')
  router.push('/login')
  return false
}

const sendMessage = async () => {
  const query = input.value.trim()
  if (!query || loading.value || !ensureLogin()) return

  messages.value.push({ id: crypto.randomUUID(), role: 'user', content: query })
  const assistant = { id: crypto.randomUUID(), role: 'assistant', content: '', loading: true }
  messages.value.push(assistant)
  input.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const response = await fetch(apiConfig.endpoints.agentQueryStream, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ query, session_id: sessionId.value || undefined }),
    })

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || `请求失败：${response.status}`)
      }

    assistant.loading = false
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (!raw) continue
        const json = JSON.parse(raw)

        if (json.type === 'response') {
          assistant.content += json.content || ''
          if (json.session_id) sessionId.value = json.session_id
        }
        if (json.type === 'done' && json.session_id) {
          sessionId.value = json.session_id
          if (!route.params.sessionId) router.replace(`/aichat/${json.session_id}`)
        }
        if (json.type === 'error') throw new Error(json.content || '生成失败')
      }
      await scrollToBottom()
    }

    if (!assistant.content) assistant.content = '没有收到内容，请稍后再试。'
  } catch (error) {
    assistant.loading = false
    assistant.content = friendlyError(error.message)
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const loadSession = async (id) => {
  if (!id || !ensureLogin()) return
  const result = await sessionStore.getSession(id)
  if (!result.success) {
    showToast(result.message)
    return
  }
  sessionId.value = id
  const history = result.data.history || []
  messages.value = history.length
    ? history.flatMap(([user, assistant]) => [
        { id: crypto.randomUUID(), role: 'user', content: user },
        { id: crypto.randomUUID(), role: 'assistant', content: assistant },
      ])
    : messages.value
  await scrollToBottom()
}

const newChat = () => {
  sessionId.value = ''
  messages.value = [
    { id: crypto.randomUUID(), role: 'assistant', content: '新会话已准备好。把问题发过来吧。' },
  ]
  router.push('/aichat')
}

const uploadFiles = async (event) => {
  if (!ensureLogin()) return
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  uploading.value = true
  try {
    const formData = new FormData()
    files.forEach((file) => formData.append(files.length > 1 ? 'files' : 'file', file))
    const endpoint = files.length > 1 ? apiConfig.endpoints.uploadMultipleFiles : apiConfig.endpoints.uploadSingleFile
    const response = await fetch(endpoint, { method: 'POST', headers: authHeaders(), body: formData })
    if (!response.ok) throw new Error('上传失败')
    await loadUploadedFiles()
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'assistant',
      content: `已上传 ${files.length} 个文件到资料库：${files.map((file) => file.name).join('、')}。现在可以直接围绕这些资料提问。`,
    })
    await scrollToBottom()
    showToast('资料已进入知识库')
  } catch (error) {
    showToast(error.message || '上传失败')
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

const cleanVectors = async () => {
  if (!ensureLogin()) return
  try {
    const response = await fetch(apiConfig.endpoints.cleanVectors, { method: 'DELETE', headers: authHeaders() })
    if (!response.ok) throw new Error('清空失败')
    uploadedFiles.value = []
    saveUploadedFiles()
    showToast('向量库已清空')
  } catch (error) {
    showToast(error.message || '清空失败')
  }
}

watch(() => route.params.sessionId, (id) => {
  if (id) loadSession(id)
})

onMounted(() => {
  if (route.params.sessionId) loadSession(route.params.sessionId)
})
</script>

<style scoped>
.chat-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 18px;
  height: 100vh;
}

.chat-main {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-height: calc(100vh - 48px);
  overflow: hidden;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.eyebrow {
  color: var(--accent);
  font-weight: 700;
  font-size: 13px;
}

.chat-header h2 {
  margin: 6px 0 4px;
  font-size: 28px;
}

.chat-header p {
  margin: 0;
  color: var(--muted);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.messages {
  overflow-y: auto;
  padding: 20px;
}

.message-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.message-row.user {
  grid-template-columns: minmax(0, 1fr) 38px;
}

.message-row.user .avatar {
  grid-column: 2;
}

.message-row.user .bubble {
  grid-column: 1;
  grid-row: 1;
  justify-self: end;
  background: #113d35;
  color: #fff;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: var(--radius);
  background: #e7ece8;
  display: grid;
  place-items: center;
  font-weight: 800;
}

.bubble {
  max-width: 900px;
  border: 1px solid var(--line);
  background: #fff;
  border-radius: var(--radius);
  padding: 13px 15px;
  line-height: 1.7;
}

.typing {
  color: var(--muted);
}

.markdown :deep(p) {
  margin: 0 0 10px;
}

.markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown :deep(pre) {
  overflow-x: auto;
  padding: 12px;
  border-radius: var(--radius);
  background: #1f2724;
  color: #eef5f1;
}

.composer {
  border-top: 1px solid var(--line);
  padding: 14px;
  background: #f9fbf8;
}

.composer textarea {
  resize: none;
}

.composer-footer {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
}

.right-rail {
  display: grid;
  gap: 18px;
  align-content: start;
}

.knowledge-panel {
  overflow: visible;
}

.rail-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rail-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.rail-body h3,
.tips-panel h3 {
  margin: 0;
}

.rail-body p {
  margin: 0;
  color: var(--muted);
}

.rail-title strong {
  min-width: 38px;
  height: 38px;
  border-radius: var(--radius);
  background: #e4f3ee;
  color: var(--accent);
  display: grid;
  place-items: center;
}

.upload-list {
  display: grid;
  gap: 8px;
  margin-top: 4px;
}

.upload-item {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fff;
  padding: 10px;
  display: grid;
  gap: 4px;
}

.upload-item span {
  font-weight: 800;
  word-break: break-all;
}

.upload-item small,
.upload-empty {
  color: var(--muted);
}

.upload-empty {
  border: 1px dashed #b9cbc2;
  border-radius: var(--radius);
  padding: 12px;
  background: #fbfdfb;
}

.hidden-input {
  display: none;
}

.tips-panel {
  padding: 16px;
}

.tip {
  width: 100%;
  text-align: left;
  margin-top: 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fff;
  padding: 12px;
  color: #39443f;
}

@media (max-width: 980px) {
  .chat-page {
    grid-template-columns: 1fr;
    height: auto;
  }

  .chat-main {
    min-height: calc(100vh - 96px);
  }

  .right-rail {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .chat-header {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .btn {
    flex: 1;
  }
}
</style>
