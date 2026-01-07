# DeepMeeting - 企业级 AI 智能会议助手

**🔒 100% 本地化部署，数据隐私零泄露！**

DeepMeeting 是一款全栈式 AI 会议解决方案。它不仅能将会议录音转录为文字并生成摘要，更内置了 **RAG (检索增强生成)** 知识库，让你的历史会议记录变成可交互、可查询的“企业大脑”。

![Architecture](https://img.shields.io/badge/Architecture-Modular-blue) ![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-green) ![License](https://img.shields.io/badge/License-MIT-orange)

## 🌟 核心功能

*   **🛡️ 极致安全**：从语音识别 (Whisper) 到大模型 (Ollama) 再到向量库 (FAISS/Chroma)，全链路离线运行，网线拔了也能用。
*   **🧠 会议知识库 (RAG)**：自动将所有会议纪要向量化存入本地数据库。你可以随时问 AI：“上个月王总关于产品定价是怎么说的？”，它会跨会议检索并回答。
*   **🖥️ 可视化 Web 界面**：内置 Streamlit 管理后台，支持上传文件、查看历史记录和智能问答。
*   **🎙️ 实时会议助手**：支持实时监听麦克风，语音转文字上屏，并自动生成纪要。
*   **📧 自动化工作流**：会议结束后自动发送邮件通知给相关人员。

## ✨ 开发工具

本项目由 **Trae IDE** 辅助开发，核心代码由 **Solo Builder** 智能生成。这展示了 AI 时代的全新开发范式：人机结对编程 (Pair Programming)。

---

## 🛠️ 技术架构

本项目采用模块化设计，易于扩展和维护：

```text
ai-meeting-assistant/
├── app/
│   ├── asr/          # 语音识别 (faster-whisper)
│   ├── llm/          # 大模型交互 (LangChain + Ollama)
│   ├── rag/          # 知识库 (FAISS/ChromaDB + SentenceTransformers)
│   ├── audio/        # 音频录制与 VAD (SoundDevice)
│   └── utils/        # 工具库
├── data/             # 数据存储 (录音、转录、向量索引)
├── web_app.py        # Streamlit Web 入口
└── main.py           # CLI 命令行入口
```

*   **ASR**: `faster-whisper` (base/small 模型)
*   **LLM**: `Ollama` (推荐 qwen2:7b)
*   **RAG**: `LangChain` + `FAISS` (向量检索)
*   **Web**: `Streamlit`

---

## 🚀 快速开始

### 1. 环境准备

**前置要求**:
*   **Python**: 3.9, 3.10 或 3.11 (暂不推荐 3.12+, 部分依赖可能未适配)
*   **操作系统**: macOS (推荐 M系列芯片), Windows, Linux

1.  **安装 Ollama** (用于运行 LLM):
    *   下载并安装 [Ollama](https://ollama.com)。
    *   拉取模型：
        *   8G 内存: `ollama run qwen2:1.5b`
        *   16G+ 内存: `ollama run qwen2:7b` (强烈推荐)

2.  **安装系统依赖**:
    *   **macOS**: `brew install portaudio ffmpeg`
    *   **Windows**: 下载 FFmpeg 并配置环境变量。

3.  **安装 Python 依赖**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

### 2. 配置项目

复制 `.env.example` 为 `.env` 并修改配置：

```ini
# 工作模式: file (文件批处理) / realtime (实时录音)
MODE=file

# LLM 设置
LLM_PROVIDER=ollama
WHISPER_MODEL_SIZE=base

# 邮件通知 (可选)
ENABLE_EMAIL_NOTIFICATION=true
EMAIL_SENDER=your_name@company.com
# ...
```

### 3. 运行使用

#### 🐳 Docker 部署（推荐）
在服务器或本地用 Docker 快速运行：
1. 构建镜像：
   - docker compose build
2. 启动服务：
   - docker compose --compatibility up -d
3. 首次拉取模型（使用本地 LLM 时）：
   - docker exec -it deepmeeting-ollama ollama pull qwen2:7b
   - docker exec -it deepmeeting-ollama ollama run qwen2:7b
4. 打开浏览器访问：
   - http://服务器IP:8502

默认会挂载以下数据卷：
- ./data 映射为 /app/data
- ./output 映射为 /app/output
环境变量从 .env 注入，可设置：
- LLM_PROVIDER, WHISPER_MODEL_SIZE, ENABLE_EMAIL_NOTIFICATION, HF_ENDPOINT, ASR_BACKEND
说明：compose 使用 --compatibility 以应用 deploy.resources.limits.memory 到非 swarm 环境。

#### 🖥️ 启动 Web 界面 (推荐)
这是最直观的使用方式，支持文件上传和知识库问答。
```bash
streamlit run web_app.py
```
浏览器访问: `http://localhost:8501`

#### 📂 批量处理文件 (CLI)
将录音文件放入 `data/` 目录，然后运行：
```bash
python3 main.py
```
程序会自动处理所有文件，生成摘要并存入知识库。

#### 🎙️ 开启实时会议
修改 `.env` 中 `MODE=realtime`，然后在终端运行：
```bash
python3 main.py
```
*注意：macOS 用户需在外部 Terminal 中运行以获取麦克风权限。*

---

## ❓ 常见问题 (FAQ)

**Q: 启动 Web 界面报错 `ModuleNotFoundError`？**
A: 请确保你已经激活了虚拟环境 (`source venv/bin/activate`) 并且执行了 `pip install -r requirements.txt`。

**Q: RAG 问答搜不到内容？**
A: 向量库需要先有数据。请先使用 Web 上传录音，或者用 CLI 模式处理一些文件，系统会自动建立索引。

**Q: 实时录音报错 `Audio Hardware Not Running`？**
A: 这是 macOS 权限问题。请不要在 IDE 内置终端运行，请打开系统自带的 Terminal.app 运行命令。
