# SQLite 数据库连接 + SQLAlchemy 配置
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 数据库文件放在 backend 目录下
# check_same_thread=False：FastAPI 是多线程的，允许跨线程使用同一个连接
SQLALCHEMY_DATABASE_URL = "sqlite:///./meeting.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# 会话工厂：后续所有数据库操作都通过 SessionLocal() 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 模型基类：models 里的表模型都继承它
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入用：每个请求拿一个独立的数据库会话，请求结束后自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """启动时创建所有表（已存在的表会跳过），并做轻量列迁移"""
    # 导入模型，让 Base.metadata 知道这些表的存在
    from app.models import meeting  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # 轻量迁移：给已有表补新列（SQLite 的 create_all 不会给旧表加列）
    # 语法：ALTER TABLE ... ADD COLUMN，列已存在时跳过
    with engine.connect() as conn:
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(meeting_result)")]
        if "sentences" not in columns:
            conn.exec_driver_sql("ALTER TABLE meeting_result ADD COLUMN sentences TEXT")
            conn.commit()
