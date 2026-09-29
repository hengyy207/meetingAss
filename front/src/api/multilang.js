// 多语言会议 API：ASR 转写（模拟）+ 翻译
import axios from 'axios'

const http = axios.create({
  baseURL: '/api',   // 经 Vite 代理转发到 http://127.0.0.1:8000
  timeout: 120000,
})

/**
 * 多语言语音转写（当前为模拟 ASR，自动识别语种）
 * @param {File} file 音频文件
 * @param {string} language 语种代码（可选，不传=自动识别混语；bo 藏语 / ug 维吾尔语 / mn 蒙古语 / kk 哈萨克语 / za 壮语 / tai 傣语）
 * @returns { message, language, text, sentences[], is_mock }
 *   sentences 每项：{ speaker_id, language, language_name, begin_time, end_time, text }
 */
export function transcribeAudio(file, language) {
  const formData = new FormData()
  formData.append('audio', file)
  if (language) formData.append('language', language)
  return http.post('/asr/transcribe', formData).then((res) => res.data)
}

/**
 * 批量逐句翻译：多语种句子 → 逐句中文（一次请求）
 * @param {string[]} texts 原语言句子列表
 * @returns { message, translations: [{ source_language, translation }] }
 */
export function translateBatch(texts) {
  return http.post('/translate/batch', { texts }).then((res) => res.data)
}

/**
 * 翻译：原语言文本 → 简体中文
 * @param {string} text 原语言文本
 * @returns { message, source_language, translation }
 */
export function translateText(text) {
  return http.post('/translate', { text }).then((res) => res.data)
}
