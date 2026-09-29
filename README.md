# AI Meeting Assistant 智能会议纪要助手

音频上传 → 语音转文字 → AI 会议总结 → 任务提取，另支持多语言会议与实时流式转写。

## 技术栈

| 端   | 技术                                              |
| --- | ----------------------------------------------- |
| 后端  | FastAPI · SQLAlchemy · SQLite · WebSocket       |
| 前端  | Vue3 · Vite · Element Plus · ECharts · Axios    |
| AI  | 百炼 Fun-ASR（转写）· MiMo（总结 / 翻译）· 流式 ASR 为 Mock 占位 |

## 环境要求

- Python 3.11+
- Node.js 18+

## 启动后端

```bash
cd backend

# 首次：创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 配置密钥：backend/.env 中填写
#   DASHSCOPE_API_KEY=...   （百炼 ASR）
#   MIMO_API_KEY=...        （MiMo 翻译/总结）
#   BASE_URL=https://...

# 启动
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后：

- API 文档：http://127.0.0.1:8000/docs
- 实时转写 WebSocket：`ws://127.0.0.1:8000/ws`

## 启动前端

```bash
cd front

# 首次安装依赖
npm install

# 启动（开发服务器，默认 5173 端口）
npm run dev
```

打开浏览器访问 **http://localhost:5173**

Vite 已配置代理：`/api` → 后端 HTTP，`/ws` → 后端 WebSocket，前端无需改后端地址。

## 页面说明

| 路由             | 页面   | 说明                                                  |
| -------------- | ---- | --------------------------------------------------- |
| `/`            | 首页   | 统计与最近会议                                             |
| `/create`      | 新建会议 | 上传音频 → 多语种转写（Mock ASR）→ MiMo 翻译 → AI 纪要             |
| `/realtime`    | 实时转写 | 麦克风实时采集 → WebSocket 流式识别 → partial/final + 翻译 + 时间轴 |
| `/history`     | 历史会议 | 列表 / 删除                                             |
| `/meeting/:id` | 会议详情 | 转写 + 摘要 + 任务                                        |

## 实时转写（/realtime）说明

**链路**：麦克风 → AudioWorklet 采集 → 重采样 16kHz/16bit/单声道 PCM → 每 100ms 经 WebSocket 发送 → 后端流式识别 → `partial`（临时，覆盖渲染）/ `final`（最终，追加 + 翻译 + 时间轴）。

**当前为 Mock 占位**（方便后续替换真实模型）：

- `backend/app/services/stream_asr_service.py` — 流式 ASR，实现 `BaseStreamASR` 接口；每 3 帧吐 partial，连续静音 3 秒吐 final。替换真实模型：实现该接口并在 `create_stream_asr()` 返回真实实例。
- `backend/app/services/stream_translation_service.py` — 流式翻译，默认 Mock（延迟 500ms）；把 `USE_REAL_TRANSLATION` 改为 `True` 即切换真实 MiMo 翻译。

**WebSocket 消息协议**（`ws://.../ws`）：

| 方向      | 帧类型 | 内容                                                                      |
| ------- | --- | ----------------------------------------------------------------------- |
| 前端 → 后端 | 二进制 | 一段完整 PCM 音频（16kHz/16bit/单声道/100ms = 3200 字节）                            |
| 前端 → 后端 | 文本  | 控制 JSON：`start` / `pause` / `resume` / `stop` / `ping`                  |
| 后端 → 前端 | 文本  | 事件 JSON：`ready` / `started` / `partial` / `final` / `stopped` / `error` |

`final` 事件结构：

```json
{"type": "final", "text": "识别原文", "translation": "中文译文",
 "language": "藏语", "speaker": "01", "startTime": 0, "endTime": 3200}
```

**粘包与重连**：WebSocket 是消息协议，消息边界由协议层保证——一次发送就是一条完整消息（前端固定 100ms/帧），接收端按消息处理，不存在 TCP 粘包问题。前端断线后按指数退避重连（1s → 2s → 4s → 8s → 10s 封顶），重连期间暂停发送音频，重连成功自动恢复会话。

## 测试脚本

```bash
cd backend

.venv\Scripts\python test_full.py     # 上传 → 转写 → 总结 全链路
.venv\Scripts\python test_llm.py      # LLM 总结服务
.venv\Scripts\python test_delete.py   # 删除接口
.venv\Scripts\python test_ws.py       # 实时转写 WebSocket（需先启动后端）
```

## 目录结构

```
meetingAss/
├── backend/
│   ├── app/
│   │   ├── api/            # Controller 层（meeting / multilang / realtime / health）
│   │   ├── services/       # Service 层（asr / llm / translation / stream_*）
│   │   ├── models/         # SQLAlchemy 模型
│   │   └── utils/          # 工具（env 加载）
│   ├── prompts/            # Prompt 模板（独立保存）
│   ├── uploads/            # 上传的音频
│   └── test_*.py           # 测试脚本
└── front/
    ├── public/             # 静态资源（worklet-processor.js 音频采集）
    └── src/
        ├── views/          # 页面
        ├── components/     # 组件
        ├── composables/    # 组合式函数（音频采集 / WebSocket）
        ├── api/            # HTTP 接口封装
        └── router/         # 路由
```
