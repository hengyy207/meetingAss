<template>
  <!-- 整体布局：左侧导航 + 右侧主区（ChatGPT 工作台式） -->
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-mark">
          <AudioLines :size="18" :stroke-width="2" />
        </span>
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
          <component :is="item.icon" class="nav-icon" :size="20" :stroke-width="1.75" />
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 已启用的小语种标签（次要信息，弱化处理） -->
      <div class="lang-panel">
        <div class="lang-title">已启用语言</div>
        <div class="lang-tags">
          <span v-for="lang in enabledLangs" :key="lang" class="lang-tag">{{ lang }}</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="new-btn" @click="$router.push('/create')">
          <Plus :size="17" :stroke-width="2.25" />
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
import { Home, Mic, AudioWaveform, History as HistoryIcon, AudioLines, Plus } from 'lucide-vue-next'

// 侧边栏菜单配置（Lucide 线性图标，统一 1.75 描边）
const menus = [
  { path: '/', icon: Home, label: '首页' },
  { path: '/create', icon: Mic, label: '新建会议' },
  { path: '/realtime', icon: AudioWaveform, label: '实时转写' },
  { path: '/history', icon: HistoryIcon, label: '历史会议' },
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

/* 品牌：主色圆角方块 + 声波图标 */
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 19px;
  font-weight: 700;
  padding: 0 12px;
  margin-bottom: 36px;
}

.logo-mark {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--color-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 导航项：浅色圆角底 + 左侧指示条 */
.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 42px;
  padding: 0 12px;
  border-radius: 12px;
  color: #4b5563;
  text-decoration: none;
  font-size: 14.5px;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

/* 选中态：浅灰圆角底 + 左侧 3px 主色指示条（不做整块黑填充） */
.nav-item-active {
  background: rgba(0, 0, 0, 0.05) !important;
  color: #111827;
  font-weight: 600;
}

.nav-item-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 18px;
  border-radius: 0 3px 3px 0;
  background: var(--color-accent);
}

/* 图标：非激活中性灰，激活近黑（与文字基线垂直居中） */
.nav-icon {
  flex-shrink: 0;
  color: #9ca3af;
  transition: color 0.15s ease;
}

.nav-item:hover .nav-icon {
  color: #6b7280;
}

.nav-item-active .nav-icon {
  color: #111827;
}

/* ===== 已启用语言标签（次要信息：小字低饱和） ===== */
.lang-panel {
  margin-top: 28px;
  padding: 0 8px;
}

.lang-title {
  font-size: 11px;
  color: var(--color-muted);
  margin-bottom: 10px;
  letter-spacing: 0.02em;
}

.lang-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.lang-tag {
  font-size: 11px;
  color: #64748b;
  background: #eef1f6;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

/* 侧边栏底部：主色实心 CTA（固定在底部） */
.sidebar-footer {
  margin-top: auto;
  padding-top: 20px;
}

.new-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 13px;
  border-radius: 12px;
  background: var(--color-accent);
  color: #fff;
  font-size: 14.5px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.15s ease;
}

.new-btn:hover {
  background: #4338ca;
}

.new-btn:active {
  transform: scale(0.98);
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

  .nav-item-active::before {
    display: none;
  }

  .lang-panel {
    display: none;
  }

  .sidebar-footer {
    margin-top: 0;
    margin-left: auto;
    padding-top: 0;
  }

  .new-btn span {
    display: none;
  }

  .main {
    padding: 24px 18px;
  }
}
</style>
