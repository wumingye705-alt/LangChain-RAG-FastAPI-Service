<template>
  <aside class="side-nav">
    <router-link class="brand" to="/aichat">
      <div class="brand-mark">R</div>
      <div>
        <h1>RAG Workspace</h1>
        <p>问答、知识库、会话管理</p>
      </div>
    </router-link>

    <nav class="nav-links">
      <router-link class="nav-link" to="/aichat"><span>问</span><span>AI 对话</span></router-link>
      <router-link class="nav-link" to="/sessions"><span>记</span><span>会话</span></router-link>
      <router-link class="nav-link" to="/my"><span>我</span><span>账户</span></router-link>
    </nav>
  </aside>
</template>
