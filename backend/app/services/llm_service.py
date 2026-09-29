# LLM 服务：调用 MiMo 大模型做会议总结 + 任务提取
#
# 链路：transcript 文本 → 填入 Prompt 模板 → 调用 MiMo（OpenAI 兼容接口）
#      → 清洗模型输出 → 解析成结构化 JSON { summary, tasks[] }
#
# 配置（backend/.env）：
#   MIMO_API_KEY  模型 API Key
#   BASE_URL      OpenAI 兼容接口地址，如 https://token-plan-cn.xiaomimimo.com/v1
import json
import os
from pathlib import Path

import requests

# 使用的 MiMo 模型（注意官方命名 2.6 与 flash 之间有连字符）
LLM_MODEL = "mimo-v2.6-flash"

# Prompt 模板路径：backend/prompts/meeting_summary.txt
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "meeting_summary.txt"


def _api_key() -> str:
    """读取 MiMo API Key（来自 .env / 环境变量）"""
    key = os.getenv("MIMO_API_KEY", "")
    if not key:
        raise RuntimeError("未配置 MIMO_API_KEY，请在 backend/.env 中设置")
    return key


def _base_url() -> str:
    """读取 OpenAI 兼容接口地址"""
    url = os.getenv("BASE_URL", "").rstrip("/")
    if not url:
        raise RuntimeError("未配置 BASE_URL，请在 backend/.env 中设置")
    return url


def _load_prompt() -> str:
    """读取会议总结 Prompt 模板"""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt 模板不存在：{PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def _parse_json(text: str) -> dict:
    """把模型输出清洗成 dict（容忍 markdown 代码块、前后多余文字）"""
    content = text.strip()

    # 去掉 ```json ... ``` 代码块围栏
    if content.startswith("```"):
        # 去掉第一行围栏和最后一行围栏
        lines = content.splitlines()
        lines = lines[1:]  # 去掉 ```json
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    # 若仍有杂文字，截取第一个 { 到最后一个 } 之间
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"模型输出中找不到 JSON：{text[:200]}")
    content = content[start : end + 1]

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"模型输出的 JSON 解析失败：{e}")


def summarize(transcript: str) -> dict:
    """对会议转录文本生成结构化纪要

    参数：
        transcript: ASR 转录出的会议文字
    返回：
        {
          "summary": {"theme": "会议主题", "points": ["要点1", "要点2"]},
          "tasks": [{"task": "...", "owner": "...", "deadline": "..."}]
        }
    """
    if not transcript or not transcript.strip():
        raise ValueError("transcript 不能为空")

    # 1. 组装 Prompt：模板 + 转录文本
    prompt = _load_prompt().replace("{transcript}", transcript.strip())

    # 2. 调用 MiMo（OpenAI 兼容 chat/completions 接口）
    resp = requests.post(
        f"{_base_url()}/chat/completions",
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "messages": [
                # system：会议秘书角色与输出格式要求（模板全文）
                {"role": "system", "content": prompt},
                # user：只需要模型处理这段转录
                {"role": "user", "content": "请生成会议纪要。"},
            ],
            "temperature": 0.3,   # 总结任务用低温度，输出更稳定
            "max_tokens": 2000,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"LLM 调用失败（HTTP {resp.status_code}）：{resp.text[:300]}")

    # 3. 取出模型回复并解析成结构化 JSON
    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"LLM 响应格式异常：{json.dumps(data, ensure_ascii=False)[:300]}")

    result = _parse_json(text)

    # 4. 兜底：保证返回结构完整
    summary = result.get("summary")
    if not isinstance(summary, dict) or "theme" not in summary:
        raise ValueError(f"LLM 输出缺少 summary.theme 字段：{result}")
    summary.setdefault("points", [])
    result.setdefault("tasks", [])
    return result
