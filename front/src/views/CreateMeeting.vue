<template>
  <!-- 新建会议：填写标题 + 上传音频 + 模拟 AI 流程 -->
  <div class="page">
    <h1 class="title">新建会议</h1>
    <p class="subtitle">填写标题，上传会议录音，AI 将自动转录并生成纪要</p>

    <!-- 上传卡片 -->
    <div class="upload-card card">
      <h2>会议信息</h2>

      <div class="field">
        <div class="field-label">会议标题</div>
        <el-input
          v-model="title"
          placeholder="例如：产品开发进度会"
          size="large"
          maxlength="50"
        />
      </div>

      <div class="field">
        <div class="field-label">会议录音</div>
        <AudioUpload v-model="file" />
      </div>

      <button
        class="btn-ink start-btn"
        :disabled="!canStart"
        @click="startAnalyze"
      >
        {{ uploading ? '上传中…' : analyzing ? 'AI 分析中…' : '开始 AI 分析' }}
      </button>
    </div>

    <!-- 上传结果：后端返回的会议信息 -->
    <div v-if="meetingInfo" class="info-card card">
      <h2>已保存到服务器</h2>
      <div class="info-row">
        <span class="info-label">会议 ID</span>
        <span class="info-value">{{ meetingInfo.id }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">文件路径</span>
        <span class="info-value">{{ meetingInfo.audio_path }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">状态</span>
        <span class="info-value">{{ meetingInfo.status }}</span>
      </div>
    </div>

    <!-- 转录结果：多语种原文 + 中文译文 -->
    <TranscriptCard
      v-if="sentences.length"
      :sentences="sentences"
      :text="transcript"
      :is-mock="true"
    />

    <!-- AI 分析结果：摘要 + 任务（LLM 真实生成） -->
    <div v-if="summary" class="result">
      <SummaryCard :summary="summary" />
      <TaskList :tasks="tasks" />
    </div>

    <!-- AI 流程：点击开始后逐步点亮 -->
    <div v-if="analyzing || done" class="flow-card card">
      <div class="flow-head">
        <h2>AI 处理流程</h2>
        <span v-if="done" class="tag-ai">已完成</span>
      </div>
      <AiFlow :active-index="flowIndex" />
    </div>

    <!-- 完成后跳转详情 -->
    <div v-if="done" class="done-row">
      <button class="btn-ink" @click="$router.push(`/meeting/${meetingInfo.id}`)">
        查看会议报告
        <ChevronRight :size="17" :stroke-width="2" style="vertical-align: -3px; margin-left: 4px" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ChevronRight } from 'lucide-vue-next'
import AudioUpload from '../components/AudioUpload.vue'
import AiFlow from '../components/AiFlow.vue'
import SummaryCard from '../components/SummaryCard.vue'
import TaskList from '../components/TaskList.vue'
import TranscriptCard from '../components/TranscriptCard.vue'
import { uploadMeeting, saveTranscript, summarizeMeeting } from '../api/meeting'
import { transcribeAudio, translateBatch } from '../api/multilang'

const title = ref('')
const file = ref(null)

// 处理状态
const uploading = ref(false)   // 正在上传文件
const analyzing = ref(false)   // 流程进行中
const done = ref(false)        // 全部完成
const flowIndex = ref(-1)      // -1 未开始，0~3 进行中，4 全部完成

// 后端返回的会议信息（上传成功后展示）
const meetingInfo = ref(null)
// ASR 转录出的文字和带说话人的句子列表
const transcript = ref('')
const sentences = ref([])
// LLM 生成的摘要和任务
const summary = ref(null)
const tasks = ref([])

// 标题和文件都填好、且不在处理中，才能开始
const canStart = computed(
  () => title.value.trim() && file.value && !uploading.value && !analyzing.value
)

// 开始处理：上传 → 多语种转写（模拟 ASR）→ LLM 翻译 → AI 总结
async function startAnalyze() {
  // ===== 第 1 步：真实上传（入库） =====
  uploading.value = true
  flowIndex.value = 0
  try {
    meetingInfo.value = await uploadMeeting(title.value.trim(), file.value)
    ElMessage.success('音频上传成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '上传失败，请重试')
    uploading.value = false
    flowIndex.value = -1
    return
  }
  uploading.value = false

  // ===== 第 2 步：语音转文字（ASR 占位：模拟识别混有多种语种的音频） =====
  analyzing.value = true
  flowIndex.value = 1
  let asr
  try {
    asr = await transcribeAudio(file.value)   // 不传语种 = 自动识别
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '语音识别失败，请重试')
    analyzing.value = false
    return
  }

  // ===== 第 3 步：LLM 翻译（真实 MiMo，逐句翻译成中文） =====
  const rawSentences = asr.sentences || []
  try {
    const tr = await translateBatch(rawSentences.map((s) => s.text))
    // 原句 + 译文合并，供转录卡片展示
    sentences.value = rawSentences.map((s, i) => ({
      ...s,
      translation: tr.translations[i]?.translation || '',
      source_language: tr.translations[i]?.source_language || s.language_name,
    }))
    // 中文译文全文（入库 + 供 AI 总结使用）；译文一般自带标点，直接拼接
    transcript.value = sentences.value.map((s) => s.translation).join('')
    ElMessage.success('识别并翻译完成')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '翻译失败，请重试')
    analyzing.value = false
    return
  }

  // ===== 第 4 步：保存转录结果到会议记录 =====
  try {
    const res = await saveTranscript(meetingInfo.value.id, transcript.value, sentences.value)
    meetingInfo.value.status = res.status  // 同步信息卡状态（pending → transcribed）
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存转录失败，请重试')
    analyzing.value = false
    return
  }

  // ===== 第 5 步：真实 AI 总结（基于中文译文生成摘要 + 任务） =====
  flowIndex.value = 2
  try {
    const res = await summarizeMeeting(meetingInfo.value.id)
    summary.value = res.summary
    tasks.value = res.tasks
    meetingInfo.value.status = res.status  // 同步信息卡状态（transcribed → done）
    ElMessage.success('AI 分析完成')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || 'AI 总结失败，请重试')
    analyzing.value = false
    return
  }

  // ===== 第 6 步：生成报告（结果已展示） =====
  flowIndex.value = 4
  analyzing.value = false
  done.value = true
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

.upload-card {
  margin-top: 36px;
}

.upload-card h2 {
  margin: 0 0 20px;
  font-size: 20px;
}

.field {
  margin-bottom: 22px;
}

.field-label {
  font-size: 13px;
  color: var(--color-muted);
  margin-bottom: 8px;
}

.start-btn {
  margin-top: 6px;
  cursor: pointer;
}

.start-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* 流程卡片 */
.flow-card {
  margin-top: 24px;
}

.flow-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 26px;
}

.flow-head h2 {
  margin: 0;
  font-size: 20px;
}

.done-row {
  margin-top: 24px;
}

/* 上传结果信息卡 */
.info-card {
  margin-top: 24px;
}

.info-card h2 {
  margin: 0 0 16px;
  font-size: 20px;
}

.info-row {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  font-size: 14px;
  border-bottom: 1px solid var(--color-line);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--color-muted);
  width: 80px;
  flex-shrink: 0;
}

.info-value {
  font-family: "SF Mono", Consolas, monospace;
  word-break: break-all;
}

/* AI 分析结果：摘要 + 任务两栏 */
.result {
  margin-top: 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

@media (max-width: 900px) {
  .result {
    grid-template-columns: 1fr;
  }
}
</style>
