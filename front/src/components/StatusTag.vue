<template>
  <!-- 会议状态标签：完成 / 处理中 / 失败 -->
  <span class="status" :class="`status-${status}`">
    <span class="status-dot"></span>
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
})

// 状态 → 文案（兼容后端完整状态机和旧的 processing）
const label = computed(
  () =>
    ({
      done: '已完成',
      failed: '处理失败',
      pending: '待处理',
      transcribing: '转录中',
      transcribed: '待总结',
      summarizing: '总结中',
      processing: '处理中',
    })[props.status] || props.status
)
</script>

<style scoped>
.status {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status-done {
  background: #eafaef;
  color: var(--color-ok);
}

.status-done .status-dot {
  background: var(--color-ok);
}

.status-processing {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.status-processing .status-dot {
  background: var(--color-accent);
}

/* 中间态（待处理/转录中/待总结/总结中）共用靛蓝样式 */
.status-pending,
.status-transcribing,
.status-transcribed,
.status-summarizing {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.status-pending .status-dot,
.status-transcribing .status-dot,
.status-transcribed .status-dot,
.status-summarizing .status-dot {
  background: var(--color-accent);
}

.status-failed {
  background: #ffeceb;
  color: var(--color-danger);
}

.status-failed .status-dot {
  background: var(--color-danger);
}
</style>
