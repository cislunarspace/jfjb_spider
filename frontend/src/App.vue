<template>
  <div class="app-layout">
    <nav class="sidebar">
      <div class="sidebar-title">报刊 PDF 助手</div>
      <router-link to="/crawl" class="nav-link" active-class="active">
        <span class="nav-icon">&#x1F4E1;</span>
        抓取
      </router-link>
      <router-link to="/results" class="nav-link" active-class="active">
        <span class="nav-icon">&#x1F4C4;</span>
        结果
      </router-link>
    </nav>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 200px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 16px 0;
  flex-shrink: 0;
}

.sidebar-title {
  padding: 8px 20px 20px;
  font-size: 16px;
  font-weight: 700;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  transition: all 0.15s;
}

.nav-link:hover {
  background: var(--bg);
  color: var(--text);
}

.nav-link.active {
  color: var(--accent);
  background: #eff6ff;
  font-weight: 600;
}

.nav-icon {
  font-size: 18px;
}

.content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}
</style>
