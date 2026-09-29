# 流式 ASR 服务（占位）：定义统一接口，当前为 Mock 实现，后续替换真实模型
#
# 职责：接收实时音频帧（PCM），模拟流式识别状态机
#   - 每收到 N 帧音频 → 生成 partial（临时结果，打字机效果）
#   - 检测到静音（连续 3 秒）或收到停止指令 → 生成 final（最终结果）
#
# 未来接入真实流式 ASR（如阿里 paraformer-realtime / 讯飞实时听写）时，
# 只需实现 BaseStreamASR 子类并替换下方工厂函数，WebSocket 层零改动。
from abc import ABC, abstractmethod

# ===== Mock 参数 =====
SAMPLE_RATE = 16000            # 采样率（前端固定发送 16000Hz / 16bit / 单声道 PCM）
BYTES_PER_FRAME = 100          # 每帧时长 100ms → 16000 * 2字节 * 0.1s = 3200 字节
FRAMES_PER_PARTIAL = 3         # 每收到 3 帧（300ms）吐一个 partial 片段
SILENCE_FRAMES_TO_FINAL = 30   # 连续静音 30 帧（3 秒）触发 final
ENERGY_THRESHOLD = 500         # Int16 平均绝对值低于此视为静音帧

# 模拟话术：轮换输出的"识别结果"（原文, 语种, 中文翻译）
# 真实 ASR 接入后此表废弃，translation 也换真实接口
MOCK_UTTERANCES = [
    {
        "text": "བཀྲ་ཤིས་བདེ་ལེགས།",
        "language": "藏语",
        "translation": "扎西德勒（吉祥如意）。",
    },
    {
        "text": "ياخشىمۇسىز.",
        "language": "维吾尔语",
        "translation": "你好。",
    },
    {
        "text": "Бүгін біз жиналыс өткіздік.",
        "language": "哈萨克语",
        "translation": "今天我们召开了会议。",
    },
    {
        "text": "Сайн байна уу.",
        "language": "蒙古语",
        "translation": "你好吗？",
    },
    {
        "text": "Mwngz ndei!",
        "language": "壮语",
        "translation": "你好！",
    },
]


class BaseStreamASR(ABC):
    """流式 ASR 服务接口：任何实现类必须提供 feed 方法"""

    @abstractmethod
    def feed(self, pcm: bytes, now_ms: int) -> dict:
        """喂入一帧音频，返回事件（无事件返回 None）

        参数：
            pcm: 一帧 PCM 二进制数据（16000Hz / 16bit / 单声道 / 100ms）
            now_ms: 距会话开始的毫秒偏移（用于记录句级时间戳）
        返回：
            None                        —— 还没有事件
            {"type": "partial", "text": "..."}
            {"type": "final", "text": "...", "translation": "...",
             "language": "...", "speaker": "01",
             "startTime": 0, "endTime": 0}
        """
        raise NotImplementedError

    @abstractmethod
    def flush(self, now_ms: int) -> dict:
        """强制结束当前未完成的识别句（停止/暂停时调用），无内容返回 None"""
        raise NotImplementedError


class MockStreamASR(BaseStreamASR):
    """Mock 流式识别：打字机式吐字 + 静音超时出 final（不调用任何模型）"""

    def __init__(self):
        # 当前正在识别的句子状态
        self._utterance_index = 0   # 轮播到第几句话术
        self._char_index = 0        # 当前已吐出的字符数
        self._sentence_start = 0    # 当前句开始时间（毫秒偏移）
        self._speaker_index = 0     # 说话人轮转 0/1/2
        # 音频帧计数
        self._feed_count = 0        # 累计收到的帧数
        self._silence_count = 0     # 连续静音帧数
        self._has_partial = False   # 当前是否有未完成的 partial

    # ---- 能量检测：判断一帧是否为静音 ----
    @staticmethod
    def _is_silence(pcm: bytes) -> bool:
        # PCM 为 16bit 小端：取所有采样点算平均绝对值
        if len(pcm) < 2:
            return True
        total = 0
        count = len(pcm) // 2
        for i in range(0, len(pcm) - 1, 2):
            sample = int.from_bytes(pcm[i:i + 2], "little", signed=True)
            total += abs(sample)
        return (total / count) < ENERGY_THRESHOLD

    def feed(self, pcm: bytes, now_ms: int) -> dict:
        self._feed_count += 1
        silent = self._is_silence(pcm)

        if silent:
            self._silence_count += 1
            # 连续静音 3 秒 → 强制 final（说话人停顿）
            if self._silence_count >= SILENCE_FRAMES_TO_FINAL and self._has_partial:
                return self.flush(now_ms)
            # 没有活跃识别句时静音帧直接忽略
            if not self._has_partial:
                return None
            return None

        # ---- 非静音帧：重置静音计数，推进识别状态机 ----
        self._silence_count = 0

        # 开新句：记录开始时间，重置吐字进度
        if not self._has_partial:
            self._has_partial = True
            self._sentence_start = now_ms
            if self._char_index >= len(self._current_utterance()["text"]):
                # 上一句吐完轮到下一句
                self._utterance_index = (self._utterance_index + 1) % len(MOCK_UTTERANCES)
            # 保证 char_index 有效
            if self._char_index > len(self._current_utterance()["text"]):
                self._char_index = 0

        # 每 N 帧吐一次 partial 片段（打字机效果）
        if self._feed_count % FRAMES_PER_PARTIAL != 0:
            return None

        text = self._current_utterance()["text"]
        # 每次推进 2 个字符，吐完为止
        self._char_index = min(self._char_index + 2, len(text))
        partial_text = text[: self._char_index]

        # 全句吐完 → 立即 final
        if self._char_index >= len(text):
            return self.flush(now_ms)

        return {"type": "partial", "text": partial_text}

    def flush(self, now_ms: int) -> dict:
        """把当前 partial 收尾为 final"""
        if not self._has_partial:
            return None

        utterance = self._current_utterance()
        full_text = utterance["text"]
        # 说话人轮转：每句换一个人（01/02/03 循环）
        speaker = f"{self._speaker_index + 1:02d}"
        self._speaker_index = (self._speaker_index + 1) % 3

        event = {
            "type": "final",
            "text": full_text,
            "translation": utterance["translation"],
            "language": utterance["language"],
            "speaker": speaker,
            "startTime": self._sentence_start,
            "endTime": now_ms,
        }

        # 重置状态，准备下一句
        self._has_partial = False
        self._char_index = 0
        self._utterance_index = (self._utterance_index + 1) % len(MOCK_UTTERANCES)
        self._silence_count = 0
        return event

    def _current_utterance(self) -> dict:
        return MOCK_UTTERANCES[self._utterance_index % len(MOCK_UTTERANCES)]


# 每个 WebSocket 连接创建独立的识别实例（状态互相隔离）
# 接入真实流式 ASR 后，把 MockStreamASR 换成真实实现类即可
def create_stream_asr() -> BaseStreamASR:
    return MockStreamASR()
