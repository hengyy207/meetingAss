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

/* 语义统一：绿 = 成功，橙 = 进行中，灰 = 等待，红 = 失败 */
.status-done {
  background: #ecfdf3;
  color: var(--color-ok);
}

.status-done .status-dot {
  background: var(--color-ok);
}

/* 进行中：转录中 / 总结中 / 处理中 */
.status-transcribing,
.status-summarizing,
.status-processing {
  background: #fef6e7;
  color: var(--color-warn);
}

.status-transcribing .status-dot,
.status-summarizing .status-dot,
.status-processing .status-dot {
  background: var(--color-warn);
}

/* 等待中：待处理 / 待总结 */
.status-pending,
.status-transcribed {
  background: #f1f1f3;
  color: var(--color-muted);
}

.status-pending .status-dot,
.status-transcribed .status-dot {
  background: var(--color-muted);
}

.status-failed {
  background: #fef0f0;
  color: var(--color-danger);
}

.status-failed .status-dot {
  background: var(--color-danger);
}
</style>
