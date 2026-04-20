<template>
  <div class="app-shell">
    <TabBar />
    <main class="page">
      <header class="topbar">
        <div>
          <h2>编辑资料</h2>
          <p>更新你的名称、手机号和简介。</p>
        </div>
        <button class="btn" @click="router.push('/my')">返回账户</button>
      </header>

      <section class="edit-grid">
        <form class="panel edit-form" @submit.prevent="saveProfile">
          <label>用户名<input v-model.trim="form.username" class="field" /></label>
          <label>手机号<input v-model.trim="form.telephone" class="field" /></label>
          <label>简介<textarea v-model.trim="form.bio" class="field" rows="5" /></label>
          <button class="btn primary" :disabled="saving">{{ saving ? '保存中' : '保存资料' }}</button>
        </form>

        <form class="panel edit-form" @submit.prevent="savePassword">
          <h3>修改密码</h3>
          <label>旧密码<input v-model="password.old" class="field" type="password" /></label>
          <label>新密码<input v-model="password.next" class="field" type="password" /></label>
          <button class="btn primary" :disabled="savingPassword">{{ savingPassword ? '更新中' : '更新密码' }}</button>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import TabBar from '../components/TabBar.vue'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const saving = ref(false)
const savingPassword = ref(false)
const form = reactive({ username: '', telephone: '', bio: '' })
const password = reactive({ old: '', next: '' })

const hydrate = async () => {
  if (!userStore.getLoginStatus) {
    router.push('/login')
    return
  }
  await userStore.getUserInfoDetail()
  const user = userStore.userInfo || {}
  form.username = user.username || ''
  form.telephone = user.telephone || ''
  form.bio = user.bio || ''
}

const saveProfile = async () => {
  saving.value = true
  const result = await userStore.updateUserInfo(form)
  saving.value = false
  showToast(result.message)
}

const savePassword = async () => {
  if (!password.old || !password.next) {
    showToast('请填写旧密码和新密码')
    return
  }
  savingPassword.value = true
  const result = await userStore.updatePassword(password.old, password.next)
  savingPassword.value = false
  showToast(result.message)
  if (result.success) {
    password.old = ''
    password.next = ''
  }
}

onMounted(hydrate)
</script>

<style scoped>
.edit-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 0.7fr);
  gap: 14px;
}

.edit-form {
  padding: 20px;
  display: grid;
  gap: 16px;
}

.edit-form h3 {
  margin: 0;
}

label {
  display: grid;
  gap: 8px;
  color: #3d4742;
  font-weight: 800;
}

textarea {
  resize: vertical;
}

@media (max-width: 860px) {
  .edit-grid {
    grid-template-columns: 1fr;
  }
}
</style>
