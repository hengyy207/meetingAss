// 通用展示格式化工具

/**
 * 会议时间展示：把 "2026-09-29 18:25:09" 格式化为 "9月29日 18:25"
 * 解析失败时原样返回，避免脏数据把列表撑破
 */
export function formatMeetingTime(timeStr) {
  if (!timeStr) return ''
  // 兼容 "2026-09-29 18:25:09" / ISO 带 T 的写法
  const m = String(timeStr).match(
    /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/
  )
  if (!m) return timeStr
  const [, , month, day, hour, minute] = m
  return `${Number(month)}月${Number(day)}日 ${hour}:${minute}`
}
