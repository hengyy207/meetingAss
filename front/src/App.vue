<template>
  <!-- 整体布局：左侧导航 + 右侧主区（ChatGPT 工作台式） -->
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-icon">🤖</span>
        <span>鸣鸟识音</span>
      </div>

      <nav class="nav">
        <router-link
          v-for="item in menus"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="nav-item-active"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 已启用的小语种标签 -->
      <div class="lang-panel">
        <div class="lang-title">已启用语言</div>
        <div class="lang-tags">
          <span v-for="lang in enabledLangs" :key="lang" class="lang-tag">{{ lang }}</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="new-btn" @click="$router.push('/create')">
          <span>＋</span>
          <span>开始新的会议</span>
        </div>
      </div>
    </aside>

    <!-- 主区域 -->
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
// 侧边栏菜单配置
const menus = [
  { path: '/', icon: '🏠', label: '首页' },
  { path: '/create', icon: '🎤', label: '新建会议' },
  { path: '/realtime', icon: '⚡', label: '实时转写' },
  { path: '/history', icon: '📚', label: '历史会议' },
]

// 已启用的小语种（侧边栏标签展示）
const enabledLangs = ['藏语', '维吾尔语', '蒙古语', '哈萨克语', '壮语', '傣语']
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--color-card);
  border-right: 1px solid var(--color-line);
  padding: 28px 20px;
  display: flex;
  flex-direction: column;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 700;
  padding: 0 12px;
  margin-bottom: 36px;
}

.logo-icon {
  font-size: 26px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 导航项：大圆角胶囊 */
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 16px;
  border-radius: 14px;
  color: var(--color-ink);
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: background 0.15s ease;
}

.nav-item:hover {
  background: #f1f1f3;
}

/* 选中态：深色胶囊 */
.nav-item-active {
  background: var(--color-ink) !important;
  color: #fff;
}

.nav-icon {
  font-size: 18px;
}

/* ===== 已启用语言标签 ===== */
.lang-panel {
  margin-top: 28px;
  padding: 0 8px;
}

.lang-title {
  font-size: 12px;
  color: var(--color-muted);
  margin-bottom: 10px;
}

.lang-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 浅蓝胶囊标签（如设计稿） */
.lang-tag {
  font-size: 12px;
  color: var(--color-accent);
  background: rgba(99, 102, 241, 0.1);
  padding: 5px 12px;
  border-radius: 999px;
  white-space: nowrap;
}

/* 侧边栏底部：新会议按钮 */
.sidebar-footer {
  margin-top: auto;
}

.new-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border-radius: 16px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.new-btn:hover {
  opacity: 0.8;
}

/* ===== 主区域 ===== */
.main {
  flex: 1;
  overflow-y: auto;
  padding: 48px 56px;
}

/* 内容统一最大宽度，居中偏左留白舒适 */
.main :deep(.page) {
  max-width: 1000px;
  margin: 0 auto;
}

/* ===== 小屏适配 ===== */
@media (max-width: 768px) {
  .layout {
    flex-direction: column;
    height: auto;
  }

  .sidebar {
    width: 100%;
    flex-direction: row;
    align-items: center;
    padding: 14px 18px;
    gap: 10px;
    overflow-x: auto;
  }

  .logo {
    margin-bottom: 0;
    white-space: nowrap;
  }

  .nav {
    flex-direction: row;
  }

  .nav-item span:last-child {
    display: none;
  }

  .sidebar-footer {
    margin-top: 0;
    margin-left: auto;
  }

  .new-btn span:last-child {
    display: none;
  }

  .main {
    padding: 24px 18px;
  }
}
</style>
