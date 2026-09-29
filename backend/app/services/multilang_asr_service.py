# 多语言 ASR 服务（占位）：定义统一接口，暂用模拟数据
#
# 目标链路：音频（混有各种语种）→ ASR 转文字（自动识别语种）→ LLM 翻译 → 中文输出
# 本模块只负责"ASR 转文字"环节，当前为 Mock 实现，不调用任何模型。
#
# 为什么不叫 asr_service.py：
#   现有 app/services/asr_service.py 是百炼 Fun-ASR 真实实现（会议链路在用），
#   多语言链路需要独立的可扩展接口，同名会冲突，故命名为 multilang_asr_service.py。
#
# 未来替换真实小语种 ASR（如讯飞藏/维/蒙/哈语识别）时，
# 只需新增一个 BaseASRService 的实现类并替换下方 asr_service 实例，接口层零改动。
from abc import ABC, abstractmethod


# 已启用的语种：代码 → 名称（前端侧边栏标签与语种徽标共用此定义）
LANGUAGES = {
    "bo": "藏语",
    "ug": "维吾尔语",
    "mn": "蒙古语",
    "kk": "哈萨克语",
    "za": "壮语",
    "tai": "傣语",
}

# 模拟识别文本：每个语种一条真实简短的问候语（占位演示用，非真实会议内容）
MOCK_TEXTS = {
    "bo": "བཀྲ་ཤིས་བདེ་ལེགས།",
    "ug": "ياخشىمۇسىز.",
    "mn": "Сайн байна уу.",
    "kk": "Сәлеметсіз бе!",
    "za": "Mwngz ndei!",
}

# 模拟"混有各种语种"的一段音频：自动识别出多说话人、多语种的句子
# （傣语暂无可靠模拟文本，仅出现在已启用语种标签中）
MOCK_SENTENCES = [
    {"speaker_id": 0, "language": "bo", "begin_time": 0, "end_time": 4200,
     "text": MOCK_TEXTS["bo"]},
    {"speaker_id": 1, "language": "ug", "begin_time": 5000, "end_time": 9800,
     "text": MOCK_TEXTS["ug"]},
    {"speaker_id": 2, "language": "kk", "begin_time": 10600, "end_time": 15200,
     "text": MOCK_TEXTS["kk"]},
    {"speaker_id": 0, "language": "mn", "begin_time": 16000, "end_time": 20400,
     "text": MOCK_TEXTS["mn"]},
    {"speaker_id": 1, "language": "za", "begin_time": 21200, "end_time": 25000,
     "text": MOCK_TEXTS["za"]},
]


class BaseASRService(ABC):
    """多语言 ASR 服务接口：任何实现类必须提供 transcribe 方法"""

    @abstractmethod
    def transcribe(self, audio_path: str, language: str = None) -> dict:
        """识别音频（支持混有多种语种），返回句子结构

        返回：
            {
              "language": "auto",          # 语种识别方式（auto = 自动识别）
              "text": "拼接的纯文本",
              "sentences": [               # 按说话人/语种切分的句子
                {"speaker_id": 0, "language": "bo", "language_name": "藏语",
                 "begin_time": 0, "end_time": 4200, "text": "..."},
                ...
              ],
              "is_mock": False
            }

        参数：
            audio_path: 音频文件路径
            language: 语种代码（bo/ug/mn/kk/za/tai），不传时自动识别（推荐，支持混语）
        """
        raise NotImplementedError


class MockASRService(BaseASRService):
    """模拟 ASR 实现：返回预设的多语种句子，供前端和翻译链路联调（不调用任何模型）"""

    def transcribe(self, audio_path: str, language: str = None) -> dict:
        # 传了指定语种时只返回该语种的句子；默认自动识别返回全部混语句子
        if language in MOCK_TEXTS:
            sentences = [s for s in MOCK_SENTENCES if s["language"] == language]
        else:
            sentences = list(MOCK_SENTENCES)

        # 每句补上语种名称，并拼接纯文本
        out_sentences = [
            {**s, "language_name": LANGUAGES[s["language"]]} for s in sentences
        ]
        text = " ".join(s["text"] for s in out_sentences)

        return {
            "language": "auto" if not language else language,
            "text": text,
            "sentences": out_sentences,
            "is_mock": True,   # 标记模拟数据，前端展示"模拟识别"角标
        }


# 当前使用模拟实现；接入真实小语种 ASR 后替换这一行即可
asr_service = MockASRService()
