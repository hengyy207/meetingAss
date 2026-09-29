# 翻译服务：调用 MiMo 大模型，把原语言文本翻译成简体中文
#
# 链路：原语言文本 → 填入翻译 Prompt 模板 → 调用 MiMo → 解析 JSON
#      → { source_language, translation }
#
# Prompt 独立保存于 backend/prompts/translation.txt
import json

import requests

# 复用 llm_service 的配置读取与 JSON 清洗（同一 MiMo 通道）
from app.services.llm_service import LLM_MODEL, _api_key, _base_url, _parse_json
from pathlib import Path

# Prompt 模板路径：backend/prompts/translation.txt
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "translation.txt"
# 逐句批量翻译 Prompt：backend/prompts/translation_segments.txt
SEGMENTS_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "translation_segments.txt"


def _load_prompt(path: Path = PROMPT_PATH) -> str:
    """读取翻译 Prompt 模板"""
    if not path.exists():
        raise FileNotFoundError(f"Prompt 模板不存在：{path}")
    return path.read_text(encoding="utf-8")


def translate(text: str) -> dict:
    """把任意语言的文本翻译成简体中文

    参数：
        text: 原语言文本（自动识别语种）
    返回：
        { "source_language": "检测到的源语言", "translation": "中文译文" }
    """
    if not text or not text.strip():
        raise ValueError("text 不能为空")

    # 1. 组装 Prompt：模板 + 待翻译文本
    prompt = _load_prompt().replace("{text}", text.strip())

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
                # system：翻译角色与输出格式要求（模板全文）
                {"role": "system", "content": prompt},
                # user：只需要模型执行翻译
                {"role": "user", "content": "请翻译。"},
            ],
            "temperature": 0.2,   # 翻译任务用更低温度，译文更稳定
            "max_tokens": 2000,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"LLM 调用失败（HTTP {resp.status_code}）：{resp.text[:300]}")

    # 3. 取出模型回复并解析
    data = resp.json()
    try:
        text_out = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"LLM 响应格式异常：{json.dumps(data, ensure_ascii=False)[:300]}")

    result = _parse_json(text_out)

    # 4. 兜底：保证返回结构完整
    return {
        "source_language": result.get("source_language", "未知"),
        "translation": result.get("translation", ""),
    }


def translate_segments(texts: list) -> list:
    """逐句翻译：一次调用翻译多句，返回与输入一一对应的译文列表

    参数：
        texts: 原语言句子列表（可混有多种语言）
    返回：
        [ {"source_language": "该句源语言", "translation": "中文译文"}, ... ]
    """
    if not texts or not any(t and t.strip() for t in texts):
        raise ValueError("texts 不能为空")

    # 1. 组装 Prompt：模板 + 逐句文本（每行一句）
    joined = "\n".join(t.strip() for t in texts)
    prompt = _load_prompt(SEGMENTS_PROMPT_PATH).replace("{texts}", joined)

    # 2. 调用 MiMo
    resp = requests.post(
        f"{_base_url()}/chat/completions",
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "请逐句翻译。"},
            ],
            "temperature": 0.2,   # 翻译任务用低温度
            "max_tokens": 2000,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"LLM 调用失败（HTTP {resp.status_code}）：{resp.text[:300]}")

    # 3. 解析
    data = resp.json()
    try:
        text_out = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"LLM 响应格式异常：{json.dumps(data, ensure_ascii=False)[:300]}")

    result = _parse_json(text_out)
    items = result.get("translations", [])

    # 4. 兜底：保证输出条数与输入一致（模型漏翻时补空）
    out = []
    for i, raw in enumerate(texts):
        item = items[i] if i < len(items) and isinstance(items[i], dict) else {}
        out.append({
            "source_language": item.get("source_language", "未知"),
            "translation": item.get("translation", raw),
        })
    return out
