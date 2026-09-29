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
        <Check v-if="i < activeIndex" class="flow-check" :size="20" :stroke-width="2.5" />
        <component v-else :is="step.icon" :size="20" :stroke-width="1.75" />
      </div>

      <!-- 节点文字 -->
      <div class="flow-label">{{ step.label }}</div>

      <!-- 连接线（最后一节不画） -->
      <div v-if="i < steps.length - 1" class="flow-line"></div>
    </div>
  </div>
</template>

<script setup>
import { Upload, Mic, Sparkles, FileText, Check } from 'lucide-vue-next'

defineProps({
  // 当前进行中的步骤下标，-1 表示未开始
  activeIndex: {
    type: Number,
    default: -1,
  },
})

// 步骤图标统一 Lucide 线性风格
const steps = [
  { icon: Upload, label: '上传音频' },
  { icon: Mic, label: '语音识别' },
  { icon: Sparkles, label: 'AI 分析' },
  { icon: FileText, label: '生成报告' },
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
  color: var(--color-muted);
  z-index: 1;
  transition: all 0.3s ease;
}

.flow-check {
  color: var(--color-ok);
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
    box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.35);
  }
  50% {
    box-shadow: 0 0 0 12px rgba(79, 70, 229, 0);
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
