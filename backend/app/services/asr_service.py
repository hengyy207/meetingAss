# ASR 服务：阿里云百炼 Fun-ASR 录音转写
#
# 完整链路（官方"本地文件→临时URL"方案）：
#   本地音频 → ①获取上传凭证 → ②传到百炼临时OSS → ③oss:// 临时URL（48小时有效）
#            → ④提交 fun-asr 异步转写任务 → ⑤轮询任务 → ⑥下载识别结果JSON → 提取文字
#
# 文档：raw/model-api-reference/more-about-models/get-temporary-file-url.md
#      raw/.../fun-asr-recorded-speech-recognition-http-api.md
import json
import os
import time
from pathlib import Path

import requests

DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/api/v1"

# 使用的 ASR 模型：通义百聆 Fun-ASR（中文/方言/抗噪，官方国内首推）
ASR_MODEL = "fun-asr"

# 转写任务轮询配置
POLL_INTERVAL = 3       # 每 3 秒查一次
POLL_TIMEOUT = 600      # 最多等 10 分钟


def _api_key() -> str:
    """读取百炼 API Key（来自 .env / 环境变量）"""
    key = os.getenv("DASHSCOPE_API_KEY", "")
    if not key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY，请在 backend/.env 中设置")
    return key


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_api_key()}"}


def upload_local_file(file_path: str, model: str = ASR_MODEL) -> str:
    """把本地文件上传到百炼临时存储，返回 oss:// 临时 URL（48 小时有效）"""
    # 1. 获取上传凭证（限流 100 QPS，demo 场景足够）
    resp = requests.get(
        f"{DASHSCOPE_BASE}/uploads",
        headers=_auth_headers(),
        params={"action": "getPolicy", "model": model},
        timeout=30,
    )
    resp.raise_for_status()
    policy = resp.json()["data"]

    # 2. 表单上传到临时 OSS（file 必须是最后一个表单域）
    file_name = Path(file_path).name
    key = f"{policy['upload_dir']}/{file_name}"

    with open(file_path, "rb") as f:
        up = requests.post(
            policy["upload_host"],
            files={
                "OSSAccessKeyId": (None, policy["oss_access_key_id"]),
                "Signature": (None, policy["signature"]),
                "policy": (None, policy["policy"]),
                "x-oss-object-acl": (None, policy["x_oss_object_acl"]),
                "x-oss-forbid-overwrite": (None, policy["x_oss_forbid_overwrite"]),
                "key": (None, key),
                "success_action_status": (None, "200"),
                "file": (file_name, f),
            },
            timeout=120,
        )
    up.raise_for_status()

    # 3. 按官方规则拼出 oss:// 临时 URL
    return f"oss://{key}"


def _submit_task(oss_url: str) -> str:
    """提交 fun-asr 异步转写任务，返回 task_id"""
    resp = requests.post(
        f"{DASHSCOPE_BASE}/services/audio/asr/transcription",
        headers={
            **_auth_headers(),
            "Content-Type": "application/json",
            # 异步任务必须开这个头
            "X-DashScope-Async": "enable",
            # 使用 oss:// 临时URL 必须开这个头，否则无法解析
            "X-DashScope-OssResourceResolve": "enable",
        },
        json={
            "model": ASR_MODEL,
            "input": {"file_urls": [oss_url]},
            "parameters": {
                # 开启说话人分离：结果 sentences 里每句会带 speaker_id
                # 注意：仅单声道音频支持，建议时长不超过 2 小时
                "diarization_enabled": True,
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["output"]["task_id"]


def _wait_task(task_id: str) -> dict:
    """轮询任务直到完成，返回任务 output"""
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        resp = requests.get(
            f"{DASHSCOPE_BASE}/tasks/{task_id}",
            headers=_auth_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        output = resp.json()["output"]
        status = output.get("task_status")

        if status == "SUCCEEDED":
            return output
        if status in ("FAILED", "CANCELED"):
            raise RuntimeError(f"转写任务失败：{json.dumps(output, ensure_ascii=False)}")

        # PENDING / RUNNING：等一会儿再查
        time.sleep(POLL_INTERVAL)

    raise RuntimeError("转写任务超时（超过 10 分钟）")


def _fetch_result(output: dict) -> dict:
    """从任务结果下载识别 JSON，提取文字 + 带说话人的句子列表"""
    results = output.get("results") or []
    if not results:
        raise RuntimeError("转写任务没有返回结果")

    # 子任务失败时有 code/message
    if results[0].get("subtask_status") != "SUCCEEDED":
        raise RuntimeError(f"转写子任务失败：{results[0].get('message', '未知错误')}")

    # transcription_url 是识别结果 JSON 的下载链接（24 小时有效）
    url = results[0].get("transcription_url")
    if not url:
        raise RuntimeError("未获取到识别结果链接")

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # 结构：transcripts[多通道].text / .sentences[]（每句带 speaker_id、begin_time、end_time）
    texts = []
    sentences = []
    for t in data.get("transcripts", []):
        texts.append(t.get("text", ""))
        for s in t.get("sentences", []):
            sentences.append({
                "speaker_id": s.get("speaker_id"),   # 说话人编号（0 起），未开启分离时为 None
                "begin_time": s.get("begin_time"),   # 开始时间（毫秒）
                "end_time": s.get("end_time"),       # 结束时间（毫秒）
                "text": s.get("text", ""),
            })

    return {
        "text": "\n".join(t for t in texts if t).strip(),
        "sentences": sentences,
    }


def transcribe(audio_path: str) -> dict:
    """转写本地音频文件，返回 { text, sentences }（同步阻塞，适合 demo 短音频）

    sentences：句子列表，每项含 speaker_id / begin_time / end_time / text
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在：{audio_path}")

    # 1. 上传拿临时 URL
    oss_url = upload_local_file(audio_path)

    # 2. 提交转写任务并等待完成
    task_id = _submit_task(oss_url)
    output = _wait_task(task_id)

    # 3. 提取文字和句子结构
    return _fetch_result(output)
