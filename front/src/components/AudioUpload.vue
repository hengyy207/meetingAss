<template>
  <!-- 音频上传区：拖入或点击选择 mp3 / wav -->
  <div
    class="upload-box"
    :class="{ 'upload-hover': dragging }"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
    @click="fileInput?.click()"
  >
    <!-- 已选文件 -->
    <div v-if="file" class="upload-file">
      <div class="upload-file-icon">🎵</div>
      <div class="upload-file-name">{{ file.name }}</div>
      <div class="upload-file-size">{{ formatSize(file.size) }}</div>
      <button class="upload-clear" @click.stop="clearFile">重新选择</button>
    </div>

    <!-- 空状态 -->
    <div v-else class="upload-empty">
      <div class="upload-icon">🎤</div>
      <div class="upload-text">拖入 mp3 / wav 文件，或点击选择</div>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept=".mp3,.wav"
      hidden
      @change="onSelect"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 选中的文件（暂存本地，暂不上传）
const file = defineModel({ default: null })

const dragging = ref(false)
const fileInput = ref(null)

// 拖拽松手
function onDrop(e) {
  dragging.value = false
  const f = e.dataTransfer.files?.[0]
  if (f) file.value = f
}

// 点击选择
function onSelect(e) {
  const f = e.target.files?.[0]
  if (f) file.value = f
}

function clearFile() {
  file.value = null
  if (fileInput.value) fileInput.value.value = ''
}

// 文件大小格式化
function formatSize(bytes) {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}
</script>

<style scoped>
.upload-box {
  height: 180px;
  border: 2px dashed var(--color-line);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-canvas);
}

.upload-box:hover,
.upload-hover {
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}

.upload-empty {
  text-align: center;
  color: var(--color-muted);
}

.upload-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.upload-text {
  font-size: 15px;
}

/* 已选文件状态 */
.upload-file {
  text-align: center;
}

.upload-file-icon {
  font-size: 36px;
}

.upload-file-name {
  font-weight: 600;
  margin-top: 8px;
  font-size: 15px;
}

.upload-file-size {
  color: var(--color-muted);
  font-size: 13px;
  margin-top: 4px;
}

.upload-clear {
  margin-top: 12px;
  background: none;
  border: none;
  color: var(--color-accent);
  cursor: pointer;
  font-size: 13px;
  text-decoration: underline;
}
</style>
