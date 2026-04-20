<template>
  <main class="auth-page register">
    <section class="auth-panel panel">
      <button class="back" @click="router.push('/login')">已有账号，去登录</button>
      <h2>创建账号</h2>
      <p>注册后可以保存会话和管理知识库。</p>

      <form @submit.prevent="submit">
        <label>用户名<input v-model.trim="form.username" class="field" placeholder="例如 zhou" /></label>
        <label>邮箱<input v-model.trim="form.email" class="field" type="email" placeholder="name@example.com" /></label>
        <label>手机号<input v-model.trim="form.telephone" class="field" placeholder="可选" /></label>
        <label>密码<input v-model="form.password" class="field" type="password" placeholder="至少 6 位" /></label>
        <label>确认密码<input v-model="form.confirm_password" class="field" type="password" placeholder="再次输入密码" /></label>
        <button class="btn primary submit" :disabled="loading">{{ loading ? '创建中' : '注册并进入' }}</button>
      </form>
    </section>

    <section class="auth-visual">
      <img src="/showcase/aichat.png" alt="AI chat preview" />
      <div>
        <span>Start clean</span>
        <h1>把前端变成好用的入口</h1>
        <p>清晰的登录、稳定的对话、直接的知识库操作。</p>
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
const form = reactive({
  username: '',
  email: '',
  telephone: '',
  password: '',
  confirm_password: '',
})

const submit = async () => {
  if (!form.username || !form.email || !form.password) {
    showToast('请填写用户名、邮箱和密码')
    return
  }
  if (form.password !== form.confirm_password) {
    showToast('两次密码不一致')
    return
  }
  loading.value = true
  const result = await userStore.register(form)
  loading.value = false
  showToast(result.message)
  if (result.success) router.push('/aichat')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(360px, 0.9fr) minmax(0, 1.1fr);
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
  gap: 14px;
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

@media (max-width: 800px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .auth-visual {
    min-height: 280px;
  }
}
</style>
