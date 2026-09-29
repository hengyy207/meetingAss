<template>
  <!-- 历史会议：卡片列表（不做传统后台表格） -->
  <div class="page">
    <h1 class="title">历史会议</h1>
    <p class="subtitle">共 {{ meetings.length }} 场会议</p>

    <!-- 列表 -->
    <div class="list">
      <div
        v-for="m in meetings"
        :key="m.id"
        class="item card"
        @click="$router.push(`/meeting/${m.id}`)"
      >
        <!-- 左侧图标 -->
        <div class="item-icon">🎙️</div>

        <!-- 中间信息 -->
        <div class="item-body">
          <div class="item-title">{{ m.title }}</div>
          <div class="item-meta">{{ m.created_time }}</div>
        </div>

        <!-- 右侧状态 + 删除 + 箭头 -->
        <StatusTag :status="m.status" />
        <button class="item-del" title="删除" @click.stop="removeMeeting(m)">删除</button>
        <div class="item-arrow">→</div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && !meetings.length" class="empty card">
      还没有会议记录，去上传第一段录音吧
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listMeetings, deleteMeeting } from '../api/meeting'
import StatusTag from '../components/StatusTag.vue'

// 会议列表（来自后端）
const meetings = ref([])
const loading = ref(true)

onMounted(load)

async function load() {
  loading.value = true
  try {
    meetings.value = await listMeetings()
  } finally {
    loading.value = false
  }
}

// 删除会议：先确认，成功后从列表移除
async function removeMeeting(m) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${m.title}」吗？转录和 AI 纪要将一并删除，无法恢复。`,
      '删除会议',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return // 用户点了取消
  }
  try {
    await deleteMeeting(m.id)
    meetings.value = meetings.value.filter((item) => item.id !== m.id)
    ElMessage.success('删除成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败，请重试')
  }
}
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

.list {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.item {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 22px 26px;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.item:hover {
  transform: translateY(-1px);
}

.item-icon {
  font-size: 28px;
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  background: var(--color-canvas);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-body {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 16px;
  font-weight: 600;
}

.item-meta {
  color: var(--color-muted);
  font-size: 13px;
  margin-top: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-arrow {
  color: var(--color-muted);
  font-size: 18px;
}

/* 删除按钮：低调显示，hover 时变红提示危险操作 */
.item-del {
  background: none;
  border: none;
  font-size: 13px;
  color: var(--color-muted);
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 8px;
  flex-shrink: 0;
}

.item-del:hover {
  color: var(--color-danger, #e5484d);
  background: rgba(229, 72, 77, 0.08);
}

.empty {
  margin-top: 32px;
  text-align: center;
  color: var(--color-muted);
  padding: 60px;
}
</style>
