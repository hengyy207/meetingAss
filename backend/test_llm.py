# 独立测试脚本：不启动 FastAPI，直接测试 llm_service
# 运行：cd backend && .venv\Scripts\python.exe test_llm.py
import json

from app.utils.env import load_env
from app.services.llm_service import summarize

# 先加载 .env（MIMO_API_KEY / BASE_URL）
load_env()

# 一段模拟的会议转录文本（中文，含摘要信息和待办事项）
SAMPLE_TRANSCRIPT = """
今天我们开了产品评审会，主要讨论新版会议助手的开发进度。
张三汇报了语音转录模块已经开发完成，准确率测试达到了百分之九十二。
李四提到前端页面还有两个 bug 需要修复，分别是上传按钮在 Safari 上无法点击，
以及转录结果卡片的样式问题。王五建议下周五之前完成全部修复工作。
另外大家一致同意在十月十五号发布第一个内测版本。
最后决定由张三负责编写发布文档，李四继续跟进前端修复。
"""

print("① 发送转录文本给 MiMo 模型生成纪要……")
result = summarize(SAMPLE_TRANSCRIPT)

print("② 模型返回的结构化 JSON：\n")
print(json.dumps(result, ensure_ascii=False, indent=2))

# 简单校验
summary = result.get("summary")
assert isinstance(summary, dict) and summary.get("theme"), "summary.theme 不合法"
assert isinstance(summary.get("points"), list) and summary["points"], "summary.points 不合法"
assert isinstance(result.get("tasks"), list), "tasks 不合法"
print(f"\n③ 校验通过：主题「{summary['theme']}」，要点 {len(summary['points'])} 条，tasks {len(result['tasks'])} 条")
