# 测试 WebSocket /ws 实时转写链路：ready → start → partial → final → pause/stop
import asyncio
import json
import math
import struct

import websockets

WS_URL = "ws://127.0.0.1:8000/ws"

# 16000Hz 16bit 单声道，100ms = 3200 字节
FRAME_BYTES = 3200


def speech_frame() -> bytes:
    """模拟说话帧：正弦波（能量高）"""
    samples = [int(6000 * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(FRAME_BYTES // 2)]
    return struct.pack(f"<{len(samples)}h", *samples)


def silence_frame() -> bytes:
    """模拟静音帧：全 0"""
    return b"\x00" * FRAME_BYTES


async def recv_until(ws, want_types, timeout=5) -> list:
    """持续接收事件直到拿到指定类型，返回期间收到的全部事件"""
    got = []
    while True:
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
        got.append(msg)
        if msg["type"] in want_types:
            return got


async def main():
    async with websockets.connect(WS_URL, max_size=None) as ws:
        # 1. 连接就绪
        ready = json.loads(await ws.recv())
        assert ready["type"] == "ready", ready
        print("① 连接 ready ✓")

        # 2. 开始会话
        await ws.send(json.dumps({"type": "start"}))
        started = json.loads(await ws.recv())
        assert started["type"] == "started", started
        print("② 会话 started ✓")

        # 3. 发送说话帧 → 收 partial（打字机渐进）
        for _ in range(6):
            await ws.send(speech_frame())
        events = await recv_until(ws, ("partial",))
        partials = [e["text"] for e in events if e["type"] == "partial"]
        assert partials, "未收到 partial 事件"
        print(f"③ partial ✓ {len(partials)} 个，渐进：{partials[0]!r} → {partials[-1]!r}")

        # 4. 发送静音帧 3 秒 → 触发 final
        for _ in range(32):
            await ws.send(silence_frame())
        events = await recv_until(ws, ("final",), timeout=8)
        final = [e for e in events if e["type"] == "final"][-1]
        for key in ("text", "translation", "speaker", "startTime", "endTime"):
            assert key in final, f"final 缺少字段 {key}"
        assert final["translation"], "translation 为空"
        print(
            f"④ 静音3秒 final ✓ speaker={final['speaker']} "
            f"原文={final['text']!r} 译文={final['translation']!r} "
            f"time=[{final['startTime']},{final['endTime']}]"
        )

        # 5. 第二句：说话 → 静音收尾，验证 speaker 轮转
        for _ in range(6):
            await ws.send(speech_frame())
        for _ in range(32):
            await ws.send(silence_frame())
        events = await recv_until(ws, ("final",), timeout=10)
        final2 = [e for e in events if e["type"] == "final"][-1]
        assert final2["speaker"] != final["speaker"], "speaker 未轮转"
        print(f"⑤ 第二句 final ✓ speaker 轮转 {final['speaker']} → {final2['speaker']}")

        # 6. 暂停 → 继续 → 结束
        await ws.send(json.dumps({"type": "pause"}))
        await ws.send(json.dumps({"type": "resume"}))
        await ws.send(json.dumps({"type": "stop"}))
        events = await recv_until(ws, ("stopped",), timeout=5)
        assert any(e["type"] == "stopped" for e in events)
        print("⑥ pause/resume/stop → stopped ✓")

    print("\n全部通过 ✓")


asyncio.run(main())
