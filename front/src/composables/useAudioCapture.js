// 麦克风采集 composable：
//   麦克风 → Float32 样本 → 重采样到 16000Hz → 16bit PCM → 每 100ms 发一帧
//
// 采集：优先 AudioWorklet（独立线程），不支持时降级 ScriptProcessor
// 重采样：请求 AudioContext({sampleRate:16000})，浏览器不遵守时线性插值手动重采样
// 发帧：缓冲满 1600 样本（100ms @16k）→ Int16 小端二进制 → onFrame 回调

const TARGET_RATE = 16000   // 目标采样率 16000Hz
const FRAME_MS = 100        // 发帧间隔 100ms
const FRAME_SAMPLES = (TARGET_RATE * FRAME_MS) / 1000 // 每帧样本数 = 1600

/**
 * 使用麦克风采集 PCM 帧
 * @param {Function} onFrame 每 100ms 回调一次，参数为 ArrayBuffer（16bit PCM）
 * @returns { start, stop, pause, resume }
 */
export function useAudioCapture(onFrame) {
  let audioContext = null
  let mediaStream = null
  let sourceNode = null
  let processorNode = null
  let workletReady = false

  let contextRate = 16000     // AudioContext 实际采样率
  let pending = new Float32Array(0)  // 重采样后待发帧的样本缓冲
  let paused = false

  // ===== 线性插值重采样 =====
  function resample(samples, fromRate, toRate) {
    if (fromRate === toRate || samples.length === 0) return samples
    const ratio = fromRate / toRate
    const newLength = Math.floor(samples.length / ratio)
    const out = new Float32Array(newLength)
    for (let i = 0; i < newLength; i++) {
      const pos = i * ratio
      const idx = Math.floor(pos)
      const frac = pos - idx
      out[i] =
        idx + 1 < samples.length
          ? samples[idx] * (1 - frac) + samples[idx + 1] * frac
          : samples[idx]
    }
    return out
  }

  // ===== Float32 → Int16 PCM（小端），凑满 1600 样本就发一帧 =====
  function appendAndEmit(floatSamples) {
    // 追加到待发缓冲
    const merged = new Float32Array(pending.length + floatSamples.length)
    merged.set(pending, 0)
    merged.set(floatSamples, pending.length)
    pending = merged

    // 每攒满一帧（1600 样本 = 100ms）发送一次
    while (pending.length >= FRAME_SAMPLES) {
      const frame = pending.slice(0, FRAME_SAMPLES)
      pending = pending.slice(FRAME_SAMPLES)

      // 暂停期间不发送（缓冲不增长，直接丢弃）
      if (paused) continue

      const pcm = new Int16Array(FRAME_SAMPLES)
      for (let i = 0; i < FRAME_SAMPLES; i++) {
        // Float32 [-1,1] → Int16 [-32768, 32767]
        const s = Math.max(-1, Math.min(1, frame[i]))
        pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff
      }
      onFrame(pcm.buffer)
    }
  }

  // ===== 采集节点接入 =====
  function connectNodes(inputNode) {
    if (workletReady) {
      // AudioWorklet：独立线程采集（推荐）
      processorNode = new AudioWorkletNode(audioContext, 'pcm-processor')
      processorNode.port.onmessage = (e) => {
        const samples = resample(e.data, contextRate, TARGET_RATE)
        appendAndEmit(samples)
      }
      inputNode.connect(processorNode)
      // ScriptProcessor 需要连到 destination 才会跑；Worklet 不需要（无需外放麦克风声音）
    } else {
      // 降级：ScriptProcessor（主线程，兼容老浏览器）
      processorNode = audioContext.createScriptProcessor(4096, 1, 1)
      processorNode.onaudioprocess = (e) => {
        const samples = resample(e.inputBuffer.getChannelData(0), contextRate, TARGET_RATE)
        appendAndEmit(samples)
      }
      inputNode.connect(processorNode)
      processorNode.connect(audioContext.destination)
    }
  }

  // ===== 开始采集 =====
  async function start() {
    if (audioContext) return

    // 1. 打开麦克风
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true },
    })

    // 2. 创建 AudioContext（请求 16k，浏览器不支持时用实际采样率 + 手动重采样）
    const Ctor = window.AudioContext || window.webkitAudioContext
    audioContext = new Ctor({ sampleRate: TARGET_RATE })
    contextRate = audioContext.sampleRate
    pending = new Float32Array(0)
    paused = false

    // 3. 尝试加载 AudioWorklet（失败则降级 ScriptProcessor）
    try {
      await audioContext.audioWorklet.addModule('/worklet-processor.js')
      workletReady = true
    } catch (e) {
      workletReady = false
    }

    // 4. 建立采集链路
    sourceNode = audioContext.createMediaStreamSource(mediaStream)
    connectNodes(sourceNode)
  }

  // ===== 暂停 / 继续 =====
  function pause() {
    paused = true
  }
  function resume() {
    paused = false
  }

  // ===== 停止并释放设备 =====
  function stop() {
    try {
      processorNode?.disconnect()
      sourceNode?.disconnect()
      mediaStream?.getTracks().forEach((t) => t.stop())
      audioContext?.close()
    } catch (e) {
      // 清理阶段的异常忽略即可
    }
    processorNode = null
    sourceNode = null
    mediaStream = null
    audioContext = null
    pending = new Float32Array(0)
  }

  return { start, stop, pause, resume }
}
