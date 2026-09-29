<template>
  <!-- 首页：工作台入口 + 统计 + 最近会议 -->
  <div class="page">
    <!-- 标题区 -->
    <h1 class="title">鸣鸟识音</h1>
    <p class="subtitle">上传一段会议录音，自动转录、总结并提取待办</p>

    <!-- 统计卡：三个安静的小卡片 -->
    <div class="stats">
      <div class="stat card">
        <div class="stat-num">{{ stats.meetingCount }}</div>
        <div class="stat-label">历史会议</div>
      </div>
      <div class="stat card">
        <div class="stat-num">{{ stats.processCount }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat card">
        <div class="stat-num">{{ stats.summaryCount }}</div>
        <div class="stat-label">AI 总结</div>
      </div>
    </div>

    <!-- 快速开始：整块可点击的工作台入口 -->
    <div class="start-card card" @click="$router.push('/create')">
      <div class="start-icon">🎤</div>
      <div class="start-body">
        <div class="start-title">开始新的会议</div>
        <div class="start-desc">拖入 mp3 / wav 文件，AI 自动完成剩下的一切</div>
      </div>
      <div class="start-arrow">→</div>
    </div>

    <!-- 最近会议 -->
    <div class="recent-head">
      <h2>最近的会议</h2>
      <router-link to="/history" class="recent-link">查看全部</router-link>
    </div>

    <div class="recent-list">
      <div
        v-for="m in recentMeetings"
        :key="m.id"
        class="recent-item card"
        @click="$router.push(`/meeting/${m.id}`)"
      >
        <div class="recent-main">
          <div class="recent-title">{{ m.title }}</div>
          <div class="recent-meta">{{ m.created_time }}</div>
        </div>
        <StatusTag :status="m.status" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { listMeetings } from '../api/meeting'
import StatusTag from '../components/StatusTag.vue'

// 会议列表（来自后端，已按创建时间倒序）
const meetings = ref([])

onMounted(async () => {
  try {
    meetings.value = await listMeetings()
  } catch {
    // 列表加载失败时静默，页面展示空状态
  }
})

// 统计：历史会议数 / 已完成数 / AI 总结数（状态 done 即已生成总结）
const stats = computed(() => ({
  meetingCount: meetings.value.length,
  processCount: meetings.value.filter((m) => m.status === 'done').length,
  summaryCount: meetings.value.filter((m) => m.status === 'done').length,
}))

// 取前 3 条作为"最近会议"
const recentMeetings = computed(() => meetings.value.slice(0, 3))
</script>

<style scoped>
.title {
  font-size: 34px;
  font-weight: 700;
  margin: 0;
}

.subtitle {
  color: var(--color-muted);
  font-size: 17px;
  margin: 10px 0 0;
}

/* ===== 统计 ===== */
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-top: 36px;
}

.stat {
  padding: 22px 26px;
}

.stat-num {
  font-size: 30px;
  font-weight: 700;
}

.stat-label {
  color: var(--color-muted);
  font-size: 13px;
  margin-top: 4px;
}

/* ===== 快速开始 ===== */
.start-card {
  margin-top: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.start-card:hover {
  transform: translateY(-2px);
}

.start-icon {
  font-size: 36px;
}

.start-title {
  font-size: 19px;
  font-weight: 600;
}

.start-desc {
  color: var(--color-muted);
  font-size: 14px;
  margin-top: 4px;
}

.start-arrow {
  margin-left: auto;
  font-size: 22px;
  color: var(--color-muted);
}

/* ===== 最近会议 ===== */
.recent-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 36px 0 14px;
}

.recent-head h2 {
  font-size: 20px;
  margin: 0;
}

.recent-link {
  color: var(--color-accent);
  text-decoration: none;
  font-size: 14px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 26px;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.recent-item:hover {
  transform: translateY(-1px);
}

.recent-title {
  font-size: 16px;
  font-weight: 600;
}

.recent-meta {
  color: var(--color-muted);
  font-size: 13px;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
