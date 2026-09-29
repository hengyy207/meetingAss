# 实时转写 WebSocket 接口：/ws
#
# 消息协议（两种帧，边界由 WebSocket 协议层保证，天然无粘包）：
#   前端 → 后端（二进制帧）：一帧 = 一段完整 PCM 音频（16000Hz / 16bit / 单声道 / 100ms）
#   前端 → 后端（文本帧）  ：JSON 控制消息 start / pause / resume / stop
#   后端 → 前端（文本帧）  ：JSON 事件 ready / partial / final / stopped / error
#
# 每个连接维护独立会话状态（识别实例、起始时间、状态机），互不干扰。
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.stream_asr_service import create_stream_asr
from app.services.stream_translation_service import create_stream_translator

router = APIRouter()


class RealtimeSession:
    """单个 WebSocket 连接的会话状态"""

    def __init__(self):
        self.asr = create_stream_asr()             # 流式识别实例（每连接独立）
        self.translator = create_stream_translator()  # 翻译实例
        self.start_monotonic = None   # 会话计时起点（收到 start 时设置）
        self.state = "idle"           # idle / running / paused
        self.partial_text = ""        # 当前未完成的 partial 内容

    def now_ms(self) -> int:
        """距会话开始的毫秒偏移"""
        if self.start_monotonic is None:
            return 0
        return int((time.monotonic() - self.start_monotonic) * 1000)

    def reset(self):
        """重新开始：重置计时与识别状态"""
        self.start_monotonic = time.monotonic()
        self.asr = create_stream_asr()
        self.state = "running"
        self.partial_text = ""

    async def handle_event(self, event: dict) -> dict:
        """处理识别事件：partial 直接转发；final 先翻译再推送"""
        if event is None:
            return None

        if event["type"] == "partial":
            self.partial_text = event["text"]
            return event

        # final：调用翻译（Mock 延迟 500ms / 可切换真实接口）
        translation = await self.translator.translate(event["text"], event.get("language", ""))
        self.partial_text = ""
        return {**event, "translation": translation}

    async def flush_partial(self) -> dict:
        """把当前未完成的 partial 收尾为 final（暂停/停止时调用）"""
        event = self.asr.flush(self.now_ms())
        return await self.handle_event(event)


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """实时转写 WebSocket：音频进、partial/final 事件出"""
    await ws.accept()
    session = RealtimeSession()

    async def send_event(event: dict):
        if event:
            await ws.send_text(json.dumps(event, ensure_ascii=False))

    async def send_error(message: str):
        await ws.send_text(json.dumps({"type": "error", "message": message}, ensure_ascii=False))

    # 连接就绪
    await send_event({"type": "ready"})

    try:
        while True:
            # 一次 receive = 一条完整消息（WebSocket 协议层保证消息边界，无 TCP 粘包问题；
            # 按序处理保证音频帧顺序）
            message = await ws.receive()

            # 对端断开：跳出循环做清理
            if message["type"] == "websocket.disconnect":
                break

            # ===== 二进制帧：PCM 音频 =====
            pcm = message.get("bytes")
            if pcm:
                if session.state != "running":
                    # 暂停/未开始时忽略音频帧
                    continue
                event = session.asr.feed(pcm, session.now_ms())
                if event and event.get("type") == "partial":
                    session.partial_text = event["text"]
                    await send_event(event)
                elif event and event.get("type") == "final":
                    await send_event(await session.handle_event(event))
                continue

            # ===== 文本帧：JSON 控制消息 =====
            text = message.get("text")
            if not text:
                continue

            try:
                cmd = json.loads(text)
            except json.JSONDecodeError:
                await send_error("收到无法解析的控制消息（已忽略）")
                continue

            ctype = cmd.get("type")

            if ctype == "start":
                # 开始/重新开始：重置会话
                session.reset()
                await send_event({"type": "started", "startTime": 0})

            elif ctype == "pause":
                # 暂停：先收尾当前 partial，再挂起状态机
                if session.state == "running":
                    await send_event(await session.flush_partial())
                    session.state = "paused"

            elif ctype == "resume":
                if session.state == "paused":
                    session.state = "running"

            elif ctype == "stop":
                # 结束：收尾 final 并回到 idle
                if session.state in ("running", "paused"):
                    await send_event(await session.flush_partial())
                session.state = "idle"
                await send_event({"type": "stopped"})

            elif ctype == "ping":
                await send_event({"type": "pong"})

    except WebSocketDisconnect:
        # 客户端异常断开（关闭标签页、网络中断等）：会话状态随连接销毁，无需额外处理
        pass
    finally:
        # 连接关闭：清理会话引用
        session.state = "idle"
        session.partial_text = ""
