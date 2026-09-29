// 实时转写 WebSocket composable：连接 /ws、收发消息、断线指数退避重连
//
// 粘包说明：WebSocket 是消息协议，帧边界由协议层保证——
//   发送端一次 send = 一条完整消息（100ms PCM 帧 / 一条 JSON），
//   接收端 onmessage 收到的也是完整消息，不存在 TCP 粘包问题；
//   文本帧用 JSON.parse 解析，二进制帧按 PCM 处理。
//
// 断线重连：非主动关闭时指数退避（1s → 2s → 4s → 8s → 10s 封顶），
//   重连期间暂停音频发送（不堆积），重连成功后回调 onReconnected 由页面恢复状态。

const BASE_URL =
  (location.protocol === 'https:' ? 'wss://' : 'ws://') +
  location.host +
  '/ws'

const MAX_RETRY_DELAY = 10000  // 重连间隔封顶 10 秒

export function useRealtimeWs({ onEvent, onStatus }) {
  let ws = null
  let retryCount = 0
  let retryTimer = null
  let closedByUser = false   // 用户主动关闭（结束/离开页面）→ 不重连
  let pendingState = 'idle'  // 重连成功后要恢复的状态 start / idle

  // ===== 连接 =====
  function connect() {
    ws = new WebSocket(BASE_URL)

    // 服务端 → 前端：JSON 事件（ready/partial/final/started/stopped/error）
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        onEvent?.(msg)
      } catch {
        // 非 JSON 消息忽略
      }
    }

    ws.onopen = () => {
      retryCount = 0
      onStatus?.('connected')
      // 连接成功（含首次与重连）：若会话应处于开始状态，自动补发 start
      if (pendingState === 'start') {
        sendControl('start')
      }
    }

    ws.onclose = () => {
      onStatus?.('disconnected')
      if (closedByUser) return
      scheduleReconnect()
    }

    ws.onerror = () => {
      // onerror 后必触发 onclose，重连逻辑统一放在 onclose
    }
  }

  // ===== 指数退避重连 =====
  function scheduleReconnect() {
    if (retryTimer) return
    const delay = Math.min(1000 * 2 ** retryCount, MAX_RETRY_DELAY)
    retryCount += 1
    onStatus?.('reconnecting', delay)
    retryTimer = setTimeout(() => {
      retryTimer = null
      connect()
    }, delay)
  }

  // ===== 发送 PCM 二进制帧 =====
  function sendAudio(arrayBuffer) {
    // 连接未就绪或断线期间丢弃本帧（音频帧不需要可靠，丢帧不影响识别效果）
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(arrayBuffer)
  }

  // ===== 发送 JSON 控制消息 =====
  function sendControl(type) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return false
    ws.send(JSON.stringify({ type }))
    return true
  }

  // ===== 开始（记录状态，供重连自动恢复） =====
  function start() {
    closedByUser = false
    pendingState = 'start'
    if (ws && ws.readyState === WebSocket.OPEN) {
      sendControl('start')
    } else {
      // 未连接：建立连接，onopen 成功后自动补发 start
      retryCount = 0
      connect()
    }
  }

  // ===== 暂停 / 继续 =====
  function pause() {
    sendControl('pause')
  }
  function resume() {
    sendControl('resume')
  }

  // ===== 主动结束：发送 stop 并关闭连接（不再重连） =====
  function stop() {
    closedByUser = true
    pendingState = 'idle'
    sendControl('stop')
    // 延迟关闭：等服务端回 stopped 事件
    setTimeout(() => {
      if (ws && ws.readyState <= WebSocket.OPEN) ws.close()
    }, 500)
  }

  // ===== 释放（离开页面时调用） =====
  function dispose() {
    closedByUser = true
    if (retryTimer) {
      clearTimeout(retryTimer)
      retryTimer = null
    }
    if (ws && ws.readyState <= WebSocket.OPEN) ws.close()
    ws = null
  }

  return { start, stop, pause, resume, sendAudio, sendControl, dispose }
}
