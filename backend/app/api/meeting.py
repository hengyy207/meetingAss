# 会议相关接口：音频上传、语音转文字、AI 总结、查询、删除
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.meeting import Meeting, MeetingResult
from app.services import asr_service, llm_service
from app.services.file_service import save_audio

router = APIRouter()


@router.post("/meeting/upload")
async def upload_meeting(
    title: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传会议音频：保存文件 + 创建会议记录，返回会议信息"""
    # 1. 标题不能为空
    if not title.strip():
        raise HTTPException(status_code=400, detail="会议标题不能为空")

    # 2. 保存音频文件到 uploads 目录
    try:
        audio_path = await save_audio(audio)
    except ValueError as e:
        # 格式/大小不合法，返回 400
        raise HTTPException(status_code=400, detail=str(e))

    # 3. 创建会议记录（状态先置为 pending，等后续 ASR 处理）
    meeting = Meeting(title=title.strip(), audio_path=audio_path, status="pending")
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # 4. 返回结果
    return {
        "message": "上传成功",
        "id": meeting.id,
        "title": meeting.title,
        "audio_path": meeting.audio_path,
        "status": meeting.status,
        "created_time": meeting.created_time.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.post("/meeting/{meeting_id}/transcribe")
def transcribe_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """语音转文字：对已上传的会议音频调用 ASR，把文字存入 meeting_result"""
    # 1. 找到会议记录
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    # 2. 音频文件必须已上传（audio_path 是相对路径，如 uploads/xxx.wav）
    audio_file = Path(__file__).resolve().parents[2] / meeting.audio_path
    if not audio_file.exists():
        raise HTTPException(status_code=400, detail="音频文件不存在，请重新上传")

    # 3. 状态置为"转录中"
    meeting.status = "transcribing"
    db.commit()

    try:
        # 4. 调用 ASR 服务（百炼 Fun-ASR，已开启说话人分离），拿到文字和句子列表
        data = asr_service.transcribe(str(audio_file))
    except Exception as e:
        # 失败：状态置 failed，把错误原因返回
        meeting.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"语音识别失败：{e}")

    # 5. 保存文字和句子结构到 meeting_result（没有记录就新建）
    result = db.query(MeetingResult).filter_by(meeting_id=meeting.id).first()
    if not result:
        result = MeetingResult(meeting_id=meeting.id)
        db.add(result)
    result.transcript = data["text"]
    result.sentences = json.dumps(data["sentences"], ensure_ascii=False)

    # 6. 状态置为"转录完成"（下一步是 AI 总结）
    meeting.status = "transcribed"
    db.commit()

    return {
        "message": "转录完成",
        "id": meeting.id,
        "status": meeting.status,
        "transcript": data["text"],
        "sentences": data["sentences"],
    }


@router.post("/meeting/{meeting_id}/transcript")
def save_transcript(meeting_id: int, payload: dict, db: Session = Depends(get_db)):
    """保存转录结果（多语言链路用）：把中文译文和原语种句子存入 meeting_result

    请求体：{ "transcript": "中文译文全文", "sentences": [{...原语种句子...}] }
    """
    # 1. 找到会议记录
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    transcript = (payload.get("transcript") or "").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript 不能为空")

    # 2. 保存到 meeting_result（没有记录就新建）
    result = db.query(MeetingResult).filter_by(meeting_id=meeting.id).first()
    if not result:
        result = MeetingResult(meeting_id=meeting.id)
        db.add(result)
    result.transcript = transcript
    result.sentences = json.dumps(payload.get("sentences") or [], ensure_ascii=False)

    # 3. 状态置为"转录完成"（下一步是 AI 总结）
    meeting.status = "transcribed"
    db.commit()

    return {
        "message": "转录已保存",
        "id": meeting.id,
        "status": meeting.status,
    }


@router.post("/meeting/{meeting_id}/summarize")
def summarize_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """AI 总结：对转录文字调用 LLM，把摘要和任务存入 meeting_result"""
    # 1. 找到会议记录和转录结果
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    result = db.query(MeetingResult).filter_by(meeting_id=meeting.id).first()
    if not result or not result.transcript:
        raise HTTPException(status_code=400, detail="还没有转录文字，请先调用转录接口")

    # 2. 构建给 LLM 的转录文本：有句子结构时带上说话人标记，任务负责人识别更准
    if result.sentences:
        sentences = json.loads(result.sentences)
        lines = [
            f"说话人{s.get('speaker_id', 0) + 1}：{s.get('text', '')}"
            for s in sentences
        ]
        transcript_for_llm = "\n".join(lines)
    else:
        transcript_for_llm = result.transcript

    # 3. 状态置为"总结中"
    meeting.status = "summarizing"
    db.commit()

    try:
        # 4. 调用 LLM 服务（MiMo），拿到结构化纪要
        data = llm_service.summarize(transcript_for_llm)
    except Exception as e:
        meeting.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"AI 总结失败：{e}")

    # 5. 保存摘要和任务（tasks 存 JSON 字符串）
    result.summary = json.dumps(data["summary"], ensure_ascii=False)
    result.tasks = json.dumps(data["tasks"], ensure_ascii=False)

    # 6. 状态置为"完成"
    meeting.status = "done"
    db.commit()

    return {
        "message": "总结完成",
        "id": meeting.id,
        "status": meeting.status,
        "summary": data["summary"],
        "tasks": data["tasks"],
    }


@router.get("/meeting")
def list_meetings(db: Session = Depends(get_db)):
    """会议列表：按创建时间倒序，供首页/历史页使用"""
    meetings = (
        db.query(Meeting).order_by(Meeting.created_time.desc()).all()
    )
    return [
        {
            "id": m.id,
            "title": m.title,
            "status": m.status,
            "created_time": m.created_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for m in meetings
    ]


@router.get("/meeting/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """会议详情：基本信息 + 转录文字 + AI 摘要 + 任务"""
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    result = db.query(MeetingResult).filter_by(meeting_id=meeting.id).first()

    # summary/tasks/sentences 在库里是 JSON 字符串，读出来要还原成对象/数组
    summary = None
    tasks = []
    sentences = []
    if result:
        if result.summary:
            summary = json.loads(result.summary)
        if result.tasks:
            tasks = json.loads(result.tasks)
        if result.sentences:
            sentences = json.loads(result.sentences)

    return {
        "id": meeting.id,
        "title": meeting.title,
        "status": meeting.status,
        "created_time": meeting.created_time.strftime("%Y-%m-%d %H:%M:%S"),
        "transcript": result.transcript if result else None,
        "sentences": sentences,
        "summary": summary,
        "tasks": tasks,
    }


@router.delete("/meeting/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """删除会议：连带删除结果记录和音频文件"""
    # 1. 找到会议记录
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    # 2. 先记下音频路径，删库前取出（删库后对象脱管就取不到了）
    audio_path = meeting.audio_path

    # 3. 删除关联的会议结果（转录/摘要/任务）
    db.query(MeetingResult).filter_by(meeting_id=meeting.id).delete()

    # 4. 删除会议记录
    db.delete(meeting)
    db.commit()

    # 5. 最后删磁盘上的音频文件（文件删不掉不影响数据库已删，只记录不报错）
    if audio_path:
        try:
            (Path(__file__).resolve().parents[2] / audio_path).unlink(missing_ok=True)
        except OSError:
            pass

    return {"message": "删除成功", "id": meeting_id}
