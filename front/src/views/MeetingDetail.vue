<template>
  <!-- 会议详情：转录 + AI 总结 + 任务（核心页面） -->
  <div class="page">
    <!-- 头部：返回 + 标题 + 状态 -->
    <div class="head">
      <button class="back" @click="$router.push('/history')">← 返回历史会议</button>

      <div class="head-row">
        <h1 class="title">{{ meeting.title }}</h1>
        <StatusTag :status="meeting.status" />
      </div>
      <div class="meta">{{ formatMeetingTime(meeting.created_time) }}</div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="card">加载中…</div>

    <!-- 加载失败 -->
    <div v-else-if="loadError" class="card error-card">{{ loadError }}</div>

    <!-- 处理失败的提示 -->
    <div v-else-if="meeting.status === 'failed'" class="card error-card">
      这场会议处理失败了，请重新上传音频再试一次。
    </div>

    <!-- 处理中：展示 AI 流程 -->
    <div v-else-if="isProcessing" class="card">
      <div class="flow-head">
        <h2>AI 处理流程</h2>
      </div>
      <AiFlow :active-index="flowIndex" />
    </div>

    <!-- 已完成：展示完整报告 -->
    <template v-else>
      <!-- 原始转录：按说话人分段展示 -->
      <TranscriptCard :sentences="meeting.sentences || []" :text="meeting.transcript || ''" />

      <!-- AI 总结 + 任务：左右两栏 -->
      <div class="result">
        <SummaryCard v-if="meeting.summary" :summary="meeting.summary" />
        <TaskList :tasks="meeting.tasks || []" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getMeeting } from '../api/meeting'
import { formatMeetingTime } from '../utils/format'
import StatusTag from '../components/StatusTag.vue'
import SummaryCard from '../components/SummaryCard.vue'
import TaskList from '../components/TaskList.vue'
import AiFlow from '../components/AiFlow.vue'
import TranscriptCard from '../components/TranscriptCard.vue'

const route = useRoute()

// 会议详情数据（来自后端）
const meeting = ref({})
const loading = ref(true)
const loadError = ref('')

// 处理中的状态（还没走到 done）
const isProcessing = computed(() =>
  ['pending', 'transcribing', 'transcribed', 'summarizing', 'processing'].includes(
    meeting.value.status
  )
)

// 处理中状态 → AiFlow 步骤序号
const flowIndex = computed(
  () =>
    ({
      pending: 0,
      transcribing: 1,
      transcribed: 2,
      summarizing: 2,
      processing: 2,
    })[meeting.value.status] ?? 2
)

// 拉取会议详情
async function load() {
  loading.value = true
  loadError.value = ''
  try {
    meeting.value = await getMeeting(route.params.id)
  } catch (e) {
    loadError.value = e.response?.data?.detail || '加载会议详情失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
// 路由参数变化时（历史列表切到另一场会议）重新加载
watch(() => route.params.id, load)
</script>

<style scoped>
.head {
  margin-bottom: 10px;
}

.back {
  background: none;
  border: none;
  color: var(--color-accent);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  margin-bottom: 18px;
}

.head-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.title {
  font-size: 34px;
  font-weight: 700;
  margin: 0;
}

.meta {
  color: var(--color-muted);
  font-size: 15px;
  margin-top: 10px;
}

/* ===== 结果两栏 ===== */
.result {
  margin-top: 22px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

.flow-head h2 {
  margin: 0 0 26px;
  font-size: 20px;
}

.error-card {
  margin-top: 30px;
  color: var(--color-danger);
}

@media (max-width: 900px) {
  .result {
    grid-template-columns: 1fr;
  }
}
</style>
