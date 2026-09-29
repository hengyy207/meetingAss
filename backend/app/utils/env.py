# 极简 .env 加载：把 backend/.env 里的 KEY=VALUE 写入环境变量
# （已存在的环境变量不覆盖，不引入额外依赖）
import os
from pathlib import Path


def load_env():
    """读取 backend/.env 并加载到环境变量"""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # 跳过空行和注释
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
