# 多语言会议接口：ASR 转写（占位）+ 翻译
# Controller 层只做参数校验和结果组装，业务逻辑在 services 层
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services import translation_service
from app.services.multilang_asr_service import asr_service

router = APIRouter()


class TranslateRequest(BaseModel):
    """翻译请求体"""
    text: str  # 原语言文本


class TranslateBatchRequest(BaseModel):
    """批量逐句翻译请求体"""
    texts: list  # 原语言句子列表（可混有多种语言）


@router.post("/asr/transcribe")
async def asr_transcribe(
    audio: UploadFile = File(...),
    language: str = Form(None),
):
    """多语言语音转写（当前为模拟 ASR，未来替换真实模型）

    请求：multipart 表单，audio 音频文件 + language 语种代码（可选：bo/ug/mn/kk/za/tai）
    返回：{ language, text, sentences[], is_mock }，sentences 每句带语种和说话人
    """
    # 1. 校验文件非空
    if not audio.filename:
        raise HTTPException(status_code=400, detail="请上传音频文件")

    # 2. 调用 ASR 服务（当前为 Mock 实现，不调用真实模型）
    #    audio_path 传文件名占位：Mock 不读文件，真实实现需先保存音频
    result = asr_service.transcribe(audio.filename, language)

    # 3. 返回识别结果
    return {
        "message": "转写完成（模拟）",
        **result,
    }


@router.post("/translate/batch")
def translate_batch(req: TranslateBatchRequest):
    """批量逐句翻译：多语种句子列表 → 逐句中文（调用 MiMo，一次请求）

    请求：{ "texts": ["句子1", "句子2", ...] }
    返回：{ "translations": [{ "source_language", "translation" }, ...] }
    """
    # 1. 校验
    if not req.texts or not any(str(t).strip() for t in req.texts):
        raise HTTPException(status_code=400, detail="翻译文本不能为空")

    # 2. 调用翻译服务
    try:
        translations = translation_service.translate_segments([str(t) for t in req.texts])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败：{e}")

    # 3. 返回
    return {
        "message": "翻译完成",
        "translations": translations,
    }


@router.post("/translate")
def translate(req: TranslateRequest):
    """翻译：原语言文本 → 简体中文（调用 MiMo）

    请求：{ "text": "原语言文本" }
    返回：{ "source_language": "检测到的源语言", "translation": "中文译文" }
    """
    # 1. 校验文本非空
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="翻译文本不能为空")

    # 2. 调用翻译服务
    try:
        result = translation_service.translate(req.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败：{e}")

    # 3. 返回翻译结果
    return {
        "message": "翻译完成",
        **result,
    }
