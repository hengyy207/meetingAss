# 文件保存服务：把上传的音频文件存到 backend/uploads 目录
import os
import uuid
from pathlib import Path

from fastapi import UploadFile

# uploads 目录定位到 backend/uploads（本文件在 backend/app/services/ 下）
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

# 只允许这两种音频格式
ALLOWED_EXTS = {".mp3", ".wav"}

# 文件大小上限：100MB
MAX_SIZE = 100 * 1024 * 1024


async def save_audio(file: UploadFile) -> str:
    """保存音频文件，返回相对路径（如 uploads/xxx.wav）"""
    # 1. 校验扩展名
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError("只支持 mp3 / wav 格式的音频")

    # 2. 读取内容并校验大小
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise ValueError("文件超过 100MB 限制")
    if len(data) == 0:
        raise ValueError("文件内容为空")

    # 3. 确保 uploads 目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 4. 用 UUID 生成新文件名，避免重名覆盖
    filename = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / filename

    # 5. 写入磁盘
    with open(path, "wb") as f:
        f.write(data)

    # 返回相对路径（存数据库用）
    return f"uploads/{filename}"
