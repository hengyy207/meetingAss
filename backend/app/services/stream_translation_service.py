# 流式翻译服务（Mock）：final 识别结果 → 中文翻译
#
# 当前实现：延迟 500ms 模拟调用翻译 API（不消耗真实模型额度）
# 后续接入真实翻译时：
#   方式一：实现 BaseStreamTranslator 子类，内部调 translation_service.translate
#   方式二：把 USE_REAL_TRANSLATION 改为 True（见文件底部开关）
import asyncio

# Mock 翻译表：识别原文 → 中文（与 stream_asr_service 的话术配套）
MOCK_TRANSLATIONS = {
    "བཀྲ་ཤིས་བདེ་ལེགས།": "扎西德勒（吉祥如意）。",
    "ياخشىمۇسىز.": "你好。",
    "Бүгін біз жиналыс өткіздік.": "今天我们召开了会议。",
    "Сайн байна уу.": "你好吗？",
    "Mwngz ndei!": "你好！",
}


class BaseStreamTranslator:
    """流式翻译服务接口（实现类提供 async translate 方法）"""

    async def translate(self, text: str, language: str = "") -> str:
        """把一句原文翻译成中文"""
        raise NotImplementedError


class MockStreamTranslator(BaseStreamTranslator):
    """Mock 翻译：延迟 500ms + 查表返回（模拟 API 调用）"""

    async def translate(self, text: str, language: str = "") -> str:
        # 模拟网络延迟 500ms
        await asyncio.sleep(0.5)
        # 命中预设话术直接返回；否则返回占位译文
        return MOCK_TRANSLATIONS.get(text, "（模拟翻译）")


class RealStreamTranslator(BaseStreamTranslator):
    """真实翻译：调用现有 MiMo 翻译服务（预留，取消注释即可启用）"""

    async def translate(self, text: str, language: str = "") -> str:
        from app.services import translation_service
        # translation_service 是同步调用，放线程池避免阻塞事件循环
        result = await asyncio.to_thread(translation_service.translate, text)
        return result["translation"]


# ===== 开关：False 用 Mock（默认，省额度）；True 用真实 MiMo 翻译 =====
USE_REAL_TRANSLATION = False

# 每个连接可共享翻译实例（无状态），WebSocket 层通过此工厂获取
def create_stream_translator() -> BaseStreamTranslator:
    return RealStreamTranslator() if USE_REAL_TRANSLATION else MockStreamTranslator()
