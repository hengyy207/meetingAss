// AudioWorklet 处理器：从麦克风采集 PCM 样本（Float32）
// AudioWorklet 运行在独立线程，不会被页面主线程卡顿打断（优于 ScriptProcessor）
//
// 采集到的样本直接转发给主线程（postMessage），重采样在主线程的
// useAudioCapture 中统一处理（兼容未开放自定义采样率的浏览器）。

class PCMProcessor extends AudioWorkletProcessor {
  process(inputs) {
    // inputs[0][0] = 第一个输入通道（麦克风）的 Float32 样本数组
    const channel = inputs[0]
    if (channel && channel.length > 0 && channel[0].length > 0) {
      // 拷贝一份发给主线程（AudioWorklet 的 buffer 会在回调后复用，必须拷贝）
      const samples = new Float32Array(channel[0])
      this.port.postMessage(samples)
    }
    // 返回 true 保持处理器持续运行
    return true
  }
}

registerProcessor('pcm-processor', PCMProcessor)
