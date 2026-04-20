<template>
  <main class="auth-page">
    <section class="auth-visual">
      <img src="/showcase/user_service.png" alt="User service preview" />
      <div>
        <span>RAG Workspace</span>
        <h1>回到你的知识工作台</h1>
        <p>登录后继续管理会话、上传材料，并让 AI 基于资料回答。</p>
      </div>
    </section>

    <section class="auth-panel panel">
      <button class="back" @click="router.push('/aichat')">返回对话</button>
      <h2>登录</h2>
      <p>使用用户名和密码进入系统。</p>

      <form @submit.prevent="submit">
        <label>
          用户名
          <input v-model.trim="form.username" class="field" autocomplete="username" placeholder="请输入用户名" />
        </label>
        <label>
          密码
          <input v-model="form.password" class="field" type="password" autocomplete="current-password" placeholder="请输入密码" />
        </label>
        <button class="btn primary submit" :disabled="loading">
          {{ loading ? '登录中' : '登录' }}
        </button>
      </form>

      <div class="switch">
        还没有账号？
        <button @click="router.push('/register')">创建账号</button>
      </div>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const submit = async () => {
  if (!form.username || !form.password) {
    showToast('请填写用户名和密码')
    return
  }
  loading.value = true
  const result = await userStore.login(form)
  loading.value = false
  showToast(result.message)
  if (result.success) router.push('/aichat')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
}

.auth-visual {
  position: relative;
  min-height: 100vh;
  padding: 44px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
  color: #fff;
  background: #183d35;
}

.auth-visual img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.36;
}

.auth-visual div {
  position: relative;
  max-width: 560px;
}

.auth-visual span {
  font-weight: 800;
  color: #b7eadc;
}

.auth-visual h1 {
  font-size: 42px;
  line-height: 1.12;
  margin: 12px 0;
}

.auth-visual p {
  margin: 0;
  font-size: 17px;
  line-height: 1.7;
}

.auth-panel {
  align-self: center;
  width: min(440px, calc(100% - 36px));
  margin: 0 auto;
  padding: 28px;
}

.back {
  border: 0;
  background: transparent;
  color: var(--accent);
  padding: 0;
  margin-bottom: 26px;
}

.auth-panel h2 {
  margin: 0 0 8px;
  font-size: 30px;
}

.auth-panel p {
  margin: 0 0 24px;
  color: var(--muted);
}

form {
  display: grid;
  gap: 16px;
}

label {
  display: grid;
  gap: 8px;
  color: #3d4742;
  font-weight: 700;
}

.submit {
  margin-top: 8px;
}

.switch {
  margin-top: 20px;
  color: var(--muted);
}

.switch button {
  border: 0;
  background: transparent;
  color: var(--accent);
  font-weight: 800;
}

@media (max-width: 800px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .auth-visual {
    min-height: 280px;
  }
}
</style>
