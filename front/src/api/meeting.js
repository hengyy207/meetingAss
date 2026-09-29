// 会议相关 API：连接 FastAPI 后端
import axios from 'axios'

const http = axios.create({
  baseURL: '/api',   // 经 Vite 代理转发到 http://127.0.0.1:8000
  timeout: 60000,
})

/**
 * 上传会议音频
 * @param {string} title 会议标题
 * @param {File} file 音频文件（mp3/wav）
 * @returns 后端返回的会议信息 { id, title, audio_path, status, ... }
 */
export function uploadMeeting(title, file) {
  // 用 FormData 携带文件和标题（浏览器自动设置 multipart 边界）
  const formData = new FormData()
  formData.append('title', title)
  formData.append('audio', file)
  return http.post('/meeting/upload', formData).then((res) => res.data)
}

/**
 * 语音转文字：对已上传的会议调用 ASR
 * @param {number} id 会议 ID
 * @returns { message, id, status, transcript }
 */
export function transcribeMeeting(id) {
  return http.post(`/meeting/${id}/transcribe`).then((res) => res.data)
}

/**
 * AI 总结：对转录文字生成摘要和任务
 * @param {number} id 会议 ID
 * @returns { message, id, status, summary, tasks }
 */
export function summarizeMeeting(id) {
  return http.post(`/meeting/${id}/summarize`).then((res) => res.data)
}

/**
 * 保存转录结果（多语言链路用）：中文译文 + 原语种句子
 * @param {number} id 会议 ID
 * @param {string} transcript 中文译文全文
 * @param {Array} sentences 原语种句子列表
 * @returns { message, id, status }
 */
export function saveTranscript(id, transcript, sentences) {
  return http.post(`/meeting/${id}/transcript`, { transcript, sentences }).then((res) => res.data)
}

/**
 * 会议列表（按创建时间倒序）
 * @returns [{ id, title, status, created_time }]
 */
export function listMeetings() {
  return http.get('/meeting').then((res) => res.data)
}

/**
 * 会议详情（含转录文字、AI 摘要、任务）
 * @param {number} id 会议 ID
 * @returns { id, title, status, created_time, transcript, summary, tasks }
 */
export function getMeeting(id) {
  return http.get(`/meeting/${id}`).then((res) => res.data)
}

/**
 * 删除会议（连带删除转录、摘要、任务和音频文件）
 * @param {number} id 会议 ID
 * @returns { message, id }
 */
export function deleteMeeting(id) {
  return http.delete(`/meeting/${id}`).then((res) => res.data)
}
