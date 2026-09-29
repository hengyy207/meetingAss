<template>
  <!-- 转录卡片：多语种混说场景 —— 说话人 · 语种 + 原文 + 中文译文 -->
  <div class="transcript-card card">
    <div class="transcript-head">
      <h2 class="transcript-title">
        <AudioLines :size="20" :stroke-width="1.75" />
        实时转写
      </h2>
      <span v-if="isMock" class="tag-mock">模拟识别</span>
      <span v-else class="tag-ai">Fun-ASR · 说话人分离</span>
    </div>

    <!-- 有句子结构：逐句展示说话人 / 语种 / 原文 / 中文 -->
    <div v-if="turns.length" class="turns">
      <div v-for="(t, i) in turns" :key="i" class="turn">
        <!-- 头部：说话人圆点 + 说话人 · 语种 + 时间 -->
        <div class="turn-head">
          <span class="dot" :class="spClass(t.speaker_id)"></span>
          <span class="who">Speaker {{ String((t.speaker_id ?? 0) + 1).padStart(2, '0') }}</span>
          <span v-if="t.language_name" class="lang">{{ t.language_name }}</span>
          <span class="time">{{ fmtTime(t.begin_time) }}</span>
        </div>

        <!-- 原语种原文 -->
        <p class="source" :class="{ 'source-rtl': isRtl(t.language) }">{{ t.text }}</p>

        <!-- 中文译文 -->
        <p v-if="t.translation" class="zh">中文：{{ t.translation }}</p>
      </div>
    </div>

    <!-- 兜底：旧数据没有句子结构时显示纯文本 -->
    <p v-else class="source">{{ text }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { AudioLines } from 'lucide-vue-next'

const props = defineProps({
  // 句子列表：[{ speaker_id, language, language_name, begin_time, end_time, text, translation }]
  sentences: { type: Array, default: () => [] },
  // 纯文本（旧数据兜底）
  text: { type: String, default: '' },
  // 是否为模拟识别
  isMock: { type: Boolean, default: false },
})

// 把连续同一说话人同一语种的句子合并成一段"发言"
const turns = computed(() => {
  const list = []
  for (const s of props.sentences) {
    const last = list[list.length - 1]
    if (last && last.speaker_id === s.speaker_id && last.language === s.language) {
      last.text += s.text
      last.translation = [last.translation, s.translation].filter(Boolean).join(' ')
      last.end_time = s.end_time
    } else {
      list.push({ ...s })
    }
  }
  return list
})

// 说话人配色：按编号循环 4 种颜色
function spClass(id) {
  return `sp-${(id ?? 0) % 4}`
}

// 维吾尔语等从右向左书写，调整文本方向
function isRtl(lang) {
  return lang === 'ug'
}

// 毫秒转 mm:ss
function fmtTime(ms) {
  if (ms == null) return ''
  const total = Math.floor(ms / 1000)
  const m = String(Math.floor(total / 60)).padStart(2, '0')
  const s = String(total % 60).padStart(2, '0')
  return `${m}:${s}`
}
</script>

<style scoped>
.transcript-card {
  margin-top: 24px;
}

.transcript-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.transcript-head h2 {
  margin: 0;
  font-size: 20px;
}

/* 标题：图标与文字垂直居中 */
.transcript-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.transcript-title svg {
  color: var(--color-accent);
  flex-shrink: 0;
}

.tag-mock {
  font-size: 12px;
  color: #c26a0a;
  background: rgba(217, 119, 6, 0.12);
  padding: 3px 10px;
  border-radius: 999px;
}

/* 发言段 */
.turns {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

/* 头部：圆点 + 说话人 + 语种 + 时间 */
.turn-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.sp-0 { background: #6366f1; }
.sp-1 { background: #10a37f; }
.sp-2 { background: #d97706; }
.sp-3 { background: #a855f7; }

.who {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.lang {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-accent);
  background: var(--color-accent-soft);
  padding: 2px 10px;
  border-radius: 999px;
}

.time {
  font-size: 12px;
  color: var(--color-muted);
  font-family: "SF Mono", Consolas, monospace;
}

/* 原语种原文（字号大一点，贴近转写稿样式） */
.source {
  margin: 0;
  font-size: 17px;
  line-height: 1.9;
  color: var(--color-ink);
  white-space: pre-wrap;
}

/* 从右向左书写的语种（维吾尔语） */
.source-rtl {
  direction: rtl;
  text-align: right;
}

/* 中文译文 */
.zh {
  margin: 8px 0 0;
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-muted);
}
</style>
