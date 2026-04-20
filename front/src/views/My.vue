<template>
  <div class="app-shell">
    <TabBar />

    <main class="page account-page">
      <header class="topbar account-topbar">
        <div>
          <span class="eyebrow">Account</span>
          <h2>账户中心</h2>
          <p>查看登录状态、个人资料和常用入口。</p>
        </div>
        <button v-if="userStore.getLoginStatus" class="btn danger" @click="logout">退出登录</button>
      </header>

      <section class="account-grid">
        <article class="panel hero-card">
          <div class="avatar-wrap">
            <img :src="avatarUrl" alt="用户头像" />
          </div>

          <div class="profile-copy">
            <span class="status-pill">{{ userStore.getLoginStatus ? '已登录' : '未登录' }}</span>
            <h3>{{ user?.username || '访客' }}</h3>
            <p>{{ user?.email || '登录后可以保存会话、上传资料并使用个人知识库。' }}</p>
          </div>

          <div class="hero-actions">
            <button class="btn primary" @click="primaryAction">
              {{ userStore.getLoginStatus ? '编辑资料' : '去登录' }}
            </button>
            <button class="btn" @click="router.push('/aichat')">进入问答</button>
          </div>
        </article>

        <article class="panel info-card">
          <span>手机号</span>
          <strong>{{ user?.telephone || '未填写' }}</strong>
        </article>

        <article class="panel info-card">
          <span>用户 ID</span>
          <strong>{{ user?.id || user?.uuid || '登录后生成' }}</strong>
        </article>

        <article class="panel bio-card">
          <span>简介</span>
          <p>{{ user?.bio || '还没有填写简介。' }}</p>
        </article>

        <article class="panel action-card">
          <div>
            <h3>会话管理</h3>
            <p>查看已经保存的提问记录和历史回答。</p>
          </div>
          <button class="btn" @click="router.push('/sessions')">查看会话</button>
        </article>

        <article class="panel action-card">
          <div>
            <h3>资料问答</h3>
            <p>上传文档后，让系统基于知识库回答。</p>
          </div>
          <button class="btn primary" @click="router.push('/aichat')">开始提问</button>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TabBar from '../components/TabBar.vue'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const user = computed(() => userStore.userInfo)
const avatarUrl = computed(() => user.value?.avatar ? `http://localhost:8001${user.value.avatar}` : '/showcase/user_service.png')

const primaryAction = () => {
  router.push(userStore.getLoginStatus ? '/profile' : '/login')
}

const logout = async () => {
  await userStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (userStore.getLoginStatus) userStore.getUserInfoDetail()
})
</script>

<style scoped>
.account-page {
  max-width: 1320px;
}

.account-topbar {
  align-items: flex-start;
}

.eyebrow {
  color: var(--accent);
  font-size: 13px;
  font-weight: 800;
}

.account-grid {
  display: grid;
  grid-template-columns: minmax(360px, 1.15fr) repeat(2, minmax(220px, 0.7fr));
  gap: 16px;
  align-items: stretch;
}

.hero-card {
  grid-row: span 3;
  padding: 26px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 22px;
  min-height: 430px;
}

.avatar-wrap {
  width: 112px;
  height: 112px;
  border-radius: var(--radius);
  padding: 5px;
  background: #e8f3ef;
}

.avatar-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius);
  display: block;
}

.profile-copy {
  align-self: start;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: var(--radius);
  background: #e8f3ef;
  color: var(--accent);
  font-weight: 800;
}

.profile-copy h3 {
  margin: 16px 0 8px;
  font-size: 34px;
  line-height: 1.1;
  word-break: break-word;
}

.profile-copy p {
  max-width: 560px;
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
  word-break: break-word;
}

.hero-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.info-card,
.bio-card,
.action-card {
  padding: 20px;
}

.info-card {
  min-height: 128px;
  display: grid;
  align-content: space-between;
  gap: 16px;
}

.info-card span,
.bio-card span {
  color: var(--muted);
}

.info-card strong {
  font-size: 22px;
  line-height: 1.35;
  word-break: break-word;
}

.bio-card {
  grid-column: span 2;
  min-height: 130px;
  display: grid;
  gap: 14px;
}

.bio-card p {
  margin: 0;
  color: #303832;
  line-height: 1.7;
  word-break: break-word;
}

.action-card {
  min-height: 160px;
  display: grid;
  gap: 18px;
  align-content: space-between;
}

.action-card h3 {
  margin: 0 0 8px;
  font-size: 20px;
}

.action-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

@media (max-width: 1120px) {
  .account-grid {
    grid-template-columns: 1fr 1fr;
  }

  .hero-card {
    grid-column: span 2;
    grid-row: auto;
    min-height: 0;
  }
}

@media (max-width: 720px) {
  .account-grid {
    grid-template-columns: 1fr;
  }

  .hero-card,
  .bio-card {
    grid-column: auto;
  }

  .hero-actions {
    grid-template-columns: 1fr;
  }
}
</style>
