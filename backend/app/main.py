# FastAPI 应用入口
from fastapi import FastAPI

from app.utils.env import load_env

# 先加载 .env（API Key 等配置），再导入其他模块
load_env()

from app.database import init_db  # noqa: E402
from app.api import health, meeting, multilang, realtime  # noqa: E402

app = FastAPI(
    title="AI Meeting Assistant",
    description="智能会议纪要助手后端",
    version="0.1.0",
)

# 启动时初始化数据库（创建表）
init_db()

# 注册路由：统一加 /api 前缀
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(meeting.router, prefix="/api", tags=["meeting"])
app.include_router(multilang.router, prefix="/api", tags=["multilang"])
# 实时转写 WebSocket（路径为 /ws，不加 /api 前缀）
app.include_router(realtime.router)


@app.get("/")
def root():
    """根路径，简单返回服务信息"""
    return {"message": "AI Meeting Assistant API"}
