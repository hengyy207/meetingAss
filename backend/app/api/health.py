# 健康检查接口：验证服务和数据库是否正常
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """健康检查：返回服务状态和数据库连接状态"""
    # 执行一条最简单的 SQL，验证数据库连接可用
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "ok",
        "database": db_status,
    }
