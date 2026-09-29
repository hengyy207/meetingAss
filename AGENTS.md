

# 简化版项目定位

## 项目名称

# AI Meeting Assistant

智能会议纪要助手

---

# 一、最终技术架构

改成：

`用户 | | Vue3 | HTTP API | FastAPI ---------------- | | SQLite AI服务 | ---------------- | | | ASR LLM 文件存储 Whisper DeepSeek 本地`

---

## 技术栈

| 模块   | 技术                  |
| ---- | ------------------- |
| 前端   | Vue3 + Element Plus |
| 后端   | FastAPI             |
| 数据库  | SQLite              |
| ORM  | SQLAlchemy          |
| AI模型 | DeepSeek/Qwen       |
| 语音识别 | Whisper API/FunASR  |
| 文件   | 本地文件夹               |
|      | ---                 |

# 三、最终功能设计

只保留5个核心页面。

---

# 页面1：首页 Dashboard

展示：

`AI Meeting Assistant 开始新的会议 历史会议数量 处理次数 AI总结次数`

---

# 页面2：创建会议

用户输入：

`会议标题 上传音频 (mp3/wav) 开始分析`

流程：

`上传 ↓ ASR ↓ LLM ↓ 生成报告`

---

# 页面3：会议详情（核心）

展示：

## 原始转录

例如：

`00:01 Speaker1 今天讨论项目进度 00:35 Speaker2 后端接口已经完成`

---

## AI总结

卡片：

`📌会议主题 项目开发进度会议 📋核心内容 1. 完成用户模块 2. 测试接口`

---

## AI任务提取

例如：

`待办事项 ☑ 张三 完成接口测试 ☑ 李四 准备部署环境`

---

# 页面4：历史会议

列表：

`会议名称 时间 状态 项目会议1 9.28 完成 产品讨论会 9.27 完成`

---

# 页面5：设置

简单：

`模型选择 DeepSeek Qwen Prompt设置`

---

# 四、后端结构（FastAPI）

server

│

├── main.py

├── api

│
├── meeting.py

├── services

│
├── asr_service.py

│
├── llm_service.py

│
└── file_service.py

├── models

│
└── meeting.py

├── database

│
└── db.py

├── uploads

└── prompts

    └── meeting_prompt.txt

---

# 五、数据库设计

只需要两张表。

---

## meeting表

`meeting id title audio_path status created_time`

例如：

```
meeting

id

title

audio_path

status

created_time

```

---

## meeting_result

保存AI结果

`meeting_result id meeting_id transcript summary tasks`

例如：

```
meeting_result


id


meeting_id


transcript


summary


tasks
列如:{
"summary":

"讨论项目开发进度",

"tasks":

[
{
"name":"完成接口",
"owner":"张三"
}

]

}
```

---

# 六、AI服务设计

## 1. ASR

接口：

`POST /api/meeting/transcribe`

输入：

`audio`

输出：

```
{"text":

"今天讨论项目"

}
```

---

## 2. 总结

接口：

`POST /api/meeting/summary`

输入：

```
{"text":

"会议内容"

}
```

输出：

```
{"summary":

"xxx","tasks":[]}
```

---

# 七、Vue3结构

web

src

├── api

│    meeting.js

├── views

│

├── Home.vue

├── CreateMeeting.vue

├── MeetingDetail.vue

└── History.vue

├── components

│

├── AudioUpload.vue

├── SummaryCard.vue

└── TaskList.vue

---

# 八、Claude Code开发顺序

这个项目非常适合 Claude Code。

建议：

---

## Step 1

生成Vue项目

Claude：

`创建Vue3 + Element Plus项目 实现侧边栏布局 完成5个页面路由`

---

## Step 2

生成FastAPI

Claude：

`创建FastAPI项目 完成会议CRUD接口 SQLite数据库 SQLAlchemy模型`

---

## Step 3

完成上传

实现：

`Vue上传音频 ↓ FastAPI保存 ↓ 返回文件地址`

---

## Step 4

接入ASR

先不要自己训练。

直接：

`Whisper API 或者 FunASR`

---

## Step 5

接入LLM

Prompt:

`你是一名专业会议秘书。 根据会议记录生成： 1.会议摘要 2.关键决策 3.待办事项 输出JSON`

---

## Step 6

优化展示

增加：

### AI流程动画

`上传 ↓ 🎤语音识别 ↓ 🧠AI分析 ↓ 📄生成报告`

---

# 九、最终项目亮点

比赛展示重点：

不要展示：

❌ 登录

❌ CRUD

展示：

## 1. AI完整链路

`音频 ↓ ASR ↓ LLM ↓ 结构化报告`

---

## 2. Agent思想

可以包装：

`Meeting Agent Tools: - Speech Recognition Tool - Summary Tool - Task Extraction Tool`

---

## 3. Prompt工程

展示：

`会议总结Prompt 任务抽取Prompt`

---




