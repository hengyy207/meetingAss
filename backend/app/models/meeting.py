# 会议相关的数据表模型
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from app.database import Base


class Meeting(Base):
    """meeting 表：记录一次会议的基本信息"""

    __tablename__ = "meeting"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)          # 会议标题
    audio_path = Column(String(500))                     # 音频文件保存路径
    status = Column(String(20), default="pending")       # 状态：pending / transcribing / done / failed
    created_time = Column(DateTime, default=datetime.now)  # 创建时间

    def __repr__(self):
        return f"<Meeting(id={self.id}, title={self.title}, status={self.status})>"


class MeetingResult(Base):
    """meeting_result 表：保存 AI 处理结果（转录文本、总结、任务）"""

    __tablename__ = "meeting_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id"), nullable=False)  # 关联会议
    transcript = Column(Text)        # 转录文本
    sentences = Column(Text)         # 说话人分离的句子列表（JSON 字符串）
    summary = Column(Text)           # AI 总结
    tasks = Column(Text)             # 待办任务（JSON 字符串）
    created_time = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<MeetingResult(id={self.id}, meeting_id={self.meeting_id})>"
