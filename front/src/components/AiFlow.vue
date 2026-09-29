<template>
  <!--
    AI 处理流程轨道 —— 全站唯一"发光"元素
    步骤：上传音频 → 语音识别 → AI 分析 → 生成报告
    activeIndex 控制当前进行到哪一步：-1 未开始，4 全部完成
  -->
  <div class="flow">
    <div
      v-for="(step, i) in steps"
      :key="step.label"
      class="flow-step"
      :class="{
        'flow-done': i < activeIndex,
        'flow-active': i === activeIndex,
      }"
    >
      <!-- 节点圆点 -->
      <div class="flow-dot">
        <span v-if="i < activeIndex" class="flow-check">✓</span>
        <span v-else class="flow-dot-icon">{{ step.icon }}</span>
      </div>

      <!-- 节点文字 -->
      <div class="flow-label">{{ step.label }}</div>

      <!-- 连接线（最后一节不画） -->
      <div v-if="i < steps.length - 1" class="flow-line"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  // 当前进行中的步骤下标，-1 表示未开始
  activeIndex: {
    type: Number,
    default: -1,
  },
})

const steps = [
  { icon: '📁', label: '上传音频' },
  { icon: '🎤', label: '语音识别' },
  { icon: '🧠', label: 'AI 分析' },
  { icon: '📄', label: '生成报告' },
]
</script>

<style scoped>
.flow {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.flow-step {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

/* 节点圆点 */
.flow-dot {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--color-canvas);
  border: 2px solid var(--color-line);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  z-index: 1;
  transition: all 0.3s ease;
}

.flow-check {
  color: var(--color-ok);
  font-weight: 700;
  font-size: 20px;
}

/* 已完成：绿色描边 */
.flow-done .flow-dot {
  border-color: var(--color-ok);
  background: #eafaef;
}

/* 进行中：靛蓝描边 + 呼吸光晕（全站唯一动效亮点） */
.flow-active .flow-dot {
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
  animation: breathe 1.6s ease-in-out infinite;
}

@keyframes breathe {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(94, 92, 230, 0.35);
  }
  50% {
    box-shadow: 0 0 0 12px rgba(94, 92, 230, 0);
  }
}

.flow-label {
  font-size: 13px;
  color: var(--color-muted);
  font-weight: 500;
}

.flow-active .flow-label {
  color: var(--color-accent);
  font-weight: 600;
}

.flow-done .flow-label {
  color: var(--color-ink);
}

/* 连接线：绝对定位在两个节点之间 */
.flow-line {
  position: absolute;
  top: 26px;
  left: calc(50% + 30px);
  width: calc(100% - 60px);
  height: 2px;
  background: var(--color-line);
}

.flow-done .flow-line {
  background: var(--color-ok);
}

@media (prefers-reduced-motion: reduce) {
  .flow-active .flow-dot {
    animation: none;
  }
}
</style>
