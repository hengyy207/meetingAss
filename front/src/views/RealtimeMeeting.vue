<template>
  <!-- 实时转写：左侧控制区 + 中间转写列表 + 底部说话人时间轴 -->
  <div class="page">
    <!-- 顶栏 -->
    <div class="head">
      <div class="head-left">
        <AudioWaveform class="head-icon" :size="30" :stroke-width="1.75" />
        <h1 class="title">实时转写</h1>
      </div>
      <div class="head-right">
        <span class="conn" :class="`conn-${connStatus}`">{{ connText }}</span>
        <span class="timer">{{ fmtTime(elapsedMs) }}</span>
      </div>
    </div>

    <div class="main-grid">
      <!-- ===== 左侧：控制区 ===== -->
      <div class="control card">
        <h2>会话控制</h2>

        <div class="btn-group">
          <button
            class="ctl-btn start"
            :disabled="running !== 'idle'"
            @click="handleStart"
          >▶ 开始识别</button>

          <button
            class="ctl-btn pause"
            :disabled="running === 'idle'"
            @click="handlePause"
          >{{ running === 'paused' ? '▶ 继续' : '⏸ 暂停' }}</button>

          <button
            class="ctl-btn stop"
            :disabled="running === 'idle'"
            @click="handleStop"
          >■ 结束</button>
        </div>

        <!-- 会话信息 -->
        <div class="info">
          <div class="info-row">
            <span class="info-label">状态</span>
            <span>{{ stateText }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">音频格式</span>
            <span class="mono">16kHz · 16bit · 单声道</span>
          </div>
          <div class="info-row">
            <span class="info-label">发送频率</span>
            <span class="mono">100ms / 帧</span>
          </div>
          <div class="info-row">
            <span class="info-label">已识别</span>
            <span>{{ finals.length }} 句</span>
          </div>
        </div>

        <div class="tip">
          点击「开始识别」后允许麦克风权限。ASR 为模拟识别（Mock），
          未来可替换真实流式模型。
        </div>
      </div>

      <!-- ===== 中间：转写列表 ===== -->
      <div class="list card">
        <div class="list-head">
          <h2>实时转写</h2>
          <span v-if="running === 'running'" class="live-tag">● 识别中</span>
          <span v-else-if="running === 'paused'" class="paused-tag">⏸ 已暂停</span>
        </div>

        <!-- 空状态 -->
        <div v-if="!finals.length && !partialText" class="empty">
          点击左侧「开始识别」开始，说话内容会实时显示在这里
        </div>

        <!-- final 列表（追加渲染） -->
        <div v-for="(f, i) in finals" :key="i" class="utter">
          <div class="utter-head">
            <span class="dot" :class="`sp-${(i % 3)}`"></span>
            <span class="who">Speaker {{ f.speaker }}</span>
            <span v-if="f.language" class="lang">{{ f.language }}</span>
            <span class="time">{{ fmtTime(f.endTime) }}</span>
          </div>
          <p class="source">{{ f.text }}</p>
          <p v-if="f.translation" class="zh">中文：{{ f.translation }}</p>
        </div>

        <!-- partial（覆盖渲染：打字机效果） -->
        <div v-if="partialText" class="utter utter-partial">
          <div class="utter-head">
            <span class="dot dot-live"></span>
            <span class="who partial-who">识别中…</span>
          </div>
          <p class="source partial-text">{{ partialText }}<span class="caret"></span></p>
        </div>
      </div>
    </div>

    <!-- ===== 底部：说话人时间轴 ===== -->
    <SpeakerTimeline :events="finals" :now="elapsedMs" />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { AudioWaveform } from 'lucide-vue-next'
import SpeakerTimeline from '../components/SpeakerTimeline.vue'
import { useAudioCapture } from '../composables/useAudioCapture'
import { useRealtimeWs } from '../composables/useRealtimeWs'

// ===== 会话状态 =====
const running = ref('idle')        // idle / running / paused
const connStatus = ref('disconnected')  // connected / disconnected / reconnecting
const finals = ref([])             // final 事件列表（追加渲染）
const partialText = ref('')        // 当前 partial（覆盖渲染）
const elapsedMs = ref(0)           // 会话计时（毫秒）

let timer = null                   // 计时器
let startedAt = 0                  // 本次开始的时间戳

// ===== WebSocket =====
const ws = useRealtimeWs({
  onEvent(msg) {
    if (msg.type === 'partial') {
      // 临时结果：覆盖渲染
      partialText.value = msg.text
    } else if (msg.type === 'final') {
      // 最终结果：清 partial、追加列表、更新时间轴
      partialText.value = ''
      finals.value.push(msg)
    } else if (msg.type === 'started') {
      ElMessage.success('开始识别')
    } else if (msg.type === 'stopped') {
      ElMessage.success('已结束')
    } else if (msg.type === 'error') {
      ElMessage.error(msg.message)
    }
  },
  onStatus(status) {
    connStatus.value = status
    if (status === 'reconnecting') {
      ElMessage.warning('连接断开，正在重连…')
    }
  },
})

// ===== 麦克风采集（onFrame 每 100ms 发一帧 PCM） =====
const capture = useAudioCapture((pcmBuffer) => {
  ws.sendAudio(pcmBuffer)
})

// ===== 控制按钮 =====
async function handleStart() {
  // 连接 WebSocket + 开启麦克风（并行）
  ws.start()
  try {
    await capture.start()
  } catch (e) {
    ElMessage.error('无法打开麦克风，请检查浏览器权限')
    ws.stop()
    return
  }
  running.value = 'running'
  startTimer()
}

function handlePause() {
  if (running.value === 'running') {
    capture.pause()
    ws.pause()
    running.value = 'paused'
    stopTimer()
  } else if (running.value === 'paused') {
    capture.resume()
    ws.resume()
    running.value = 'running'
    startTimer()
  }
}

function handleStop() {
  capture.stop()
  ws.stop()
  running.value = 'idle'
  stopTimer()
}

// ===== 会话计时 =====
function startTimer() {
  startedAt = Date.now() - elapsedMs.value
  stopTimer()
  timer = setInterval(() => {
    elapsedMs.value = Date.now() - startedAt
  }, 500)
}
function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

// ===== 展示辅助 =====
const stateText = computed(
  () =>
    ({ idle: '待开始', running: '识别中', paused: '已暂停' })[running.value]
)

const connText = computed(
  () =>
    ({
      connected: '● 已连接',
      disconnected: '○ 未连接',
      reconnecting: '● 重连中',
    })[connStatus.value]
)

function fmtTime(ms) {
  const s = Math.floor(ms / 1000)
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

// ===== 离开页面清理 =====
onBeforeUnmount(() => {
  stopTimer()
  capture.stop()
  ws.dispose()
})
</script>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.head-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}

.title {
  font-size: 30px;
  font-weight: 700;
  margin: 0;
}

.head-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 连接状态 */
.conn {
  font-size: 13px;
  padding: 5px 14px;
  border-radius: 999px;
  background: var(--color-canvas);
}

.conn-connected { color: #10a37f; }
.conn-disconnected { color: var(--color-muted); }
.conn-reconnecting { color: #d97706; }

.timer {
  font-family: "SF Mono", Consolas, monospace;
  font-size: 17px;
  color: var(--color-ink);
}

/* ===== 主区两栏 ===== */
.main-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  margin-top: 24px;
  align-items: start;
}

/* ===== 控制区 ===== */
.control h2 {
  margin: 0 0 18px;
  font-size: 17px;
}

.btn-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ctl-btn {
  border: none;
  border-radius: 12px;
  padding: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.ctl-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.ctl-btn.start { background: var(--color-accent); color: #fff; }
.ctl-btn.pause { background: var(--color-canvas); color: var(--color-ink); }
.ctl-btn.stop { background: rgba(229, 72, 77, 0.1); color: #e5484d; }

.info {
  margin-top: 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 7px 0;
  border-bottom: 1px solid var(--color-line);
}

.info-row:last-child { border-bottom: none; }

.info-label { color: var(--color-muted); }

.mono {
  font-family: "SF Mono", Consolas, monospace;
}

.tip {
  margin-top: 16px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--color-muted);
  background: var(--color-canvas);
  border-radius: 10px;
  padding: 10px 12px;
}

/* ===== 转写列表 ===== */
.list {
  min-height: 380px;
  max-height: 560px;
  overflow-y: auto;
}

.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.list-head h2 {
  margin: 0;
  font-size: 17px;
}

.live-tag {
  font-size: 12px;
  color: #e5484d;
  animation: blink 1.4s ease-in-out infinite;
}

.paused-tag {
  font-size: 12px;
  color: var(--color-muted);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.empty {
  color: var(--color-muted);
  font-size: 14px;
  text-align: center;
  padding: 90px 20px;
}

/* 一句话（final / partial 共用） */
.utter {
  padding: 14px 0;
  border-bottom: 1px solid var(--color-line);
}

.utter:last-child { border-bottom: none; }

.utter-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
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

.dot-live { background: #e5484d; animation: blink 1s infinite; }

.who {
  font-size: 13px;
  font-weight: 600;
}

.partial-who { color: var(--color-muted); }

.lang {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-accent);
  background: var(--color-accent-soft);
  padding: 2px 9px;
  border-radius: 999px;
}

.time {
  font-size: 12px;
  color: var(--color-muted);
  font-family: "SF Mono", Consolas, monospace;
}

.source {
  margin: 0;
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-ink);
  white-space: pre-wrap;
}

.zh {
  margin: 5px 0 0;
  font-size: 14px;
  color: var(--color-muted);
}

/* partial 灰色打字机效果 */
.utter-partial { opacity: 0.75; }

.partial-text { color: var(--color-muted); font-style: italic; }

.caret {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: var(--color-accent);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.9s step-end infinite;
}

@media (max-width: 900px) {
  .main-grid { grid-template-columns: 1fr; }
}
</style>
