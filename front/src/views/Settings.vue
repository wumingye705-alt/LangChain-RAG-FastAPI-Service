<template>
  <div class="app-shell">
    <TabBar />
    <main class="page">
      <header class="topbar">
        <div>
          <h2>设置</h2>
          <p>本地开发服务状态和接口入口。</p>
        </div>
      </header>

      <section class="settings-grid">
        <article class="panel setting-card">
          <span>FastAPI</span>
          <strong>http://127.0.0.1:8000</strong>
          <a class="btn" href="http://127.0.0.1:8000/docs" target="_blank">打开接口文档</a>
        </article>
        <article class="panel setting-card">
          <span>Django</span>
          <strong>http://127.0.0.1:8001</strong>
          <a class="btn" href="http://127.0.0.1:8001/docs/" target="_blank">打开用户服务文档</a>
        </article>
        <article class="panel setting-card">
          <span>Ollama</span>
          <strong>qwen3-embedding:0.6b</strong>
          <p>后端会通过本地 11434 端口调用 embedding。</p>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup>
import TabBar from '../components/TabBar.vue'
</script>

<style scoped>
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.setting-card {
  padding: 18px;
  display: grid;
  gap: 12px;
}

.setting-card span {
  color: var(--accent);
  font-weight: 800;
}

.setting-card strong {
  font-size: 18px;
  word-break: break-word;
}

.setting-card p {
  margin: 0;
  color: var(--muted);
}
</style>
