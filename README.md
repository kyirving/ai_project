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

*   **Web**: Streamlit + streamlit-mic-recorder（客户端录音）
*   **ASR**: faster-whisper（CPU，float32）
*   **Embeddings**: FastEmbed（BAAI/bge-small-zh-v1.5，ONNX）
*   **Vector Store**: FAISS（默认）/ Chroma（可选）
*   **LLM**: Ollama（建议 qwen2:1.5b 或 qwen2:7b），也支持 OpenAI/通义/智谱

---

## 🚀 部署与运行

### 组件与模型

**核心组件**
- 前端与交互：Streamlit + streamlit-mic-recorder
- 语音识别：faster-whisper（本地离线）
- 嵌入向量：FastEmbed（bge-small-zh-v1.5）
- 向量库：FAISS（默认），可切换 Chroma
- 大模型：Ollama（qwen2 系列），也支持 OpenAI/通义/智谱

**模型选择建议**
- 16GB 服务器：qwen2:7b；资源紧时用 qwen2:1.5b
- Embeddings：bge-small-zh-v1.5（中文友好，体积适中）

---

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
- LLM_PROVIDER, WHISPER_MODEL_SIZE, ENABLE_EMAIL_NOTIFICATION, HF_ENDPOINT, ASR_BACKEND, OLLAMA_BASE_URL
说明：compose 使用 --compatibility 以应用 deploy.resources.limits.memory 到非 swarm 环境。

**容器内 LLM 连接**
- Docker 环境：`OLLAMA_BASE_URL=http://ollama:11434`
- 宿主机 Ollama：
  - macOS/Windows：`OLLAMA_BASE_URL=http://host.docker.internal:11434`
  - Linux：`OLLAMA_BASE_URL=http://服务器内网IP:11434`（如需，可添加 `extra_hosts: "host.docker.internal:host-gateway"`）

**HuggingFace 模型缓存与加速**
- 已启用持久缓存与加速下载：
  - `HF_HOME=/app/data/hf_cache`
  - `HUGGINGFACE_HUB_CACHE=/app/data/hf_cache`
  - `HF_HUB_ENABLE_HF_TRANSFER=1`
- 可选本地模型目录（避免联网下载）：
  - `FASTEMBED_MODEL_DIR=/app/data/models/bge-small-zh-v1.5`
  - 预下载示例：
    - `docker exec -it deepmeeting-app python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='BAAI/bge-small-zh-v1.5', local_dir='/app/data/models/bge-small-zh-v1.5', resume_download=True)"`

#### 国内网络构建加速与故障排查
- Dockerfile 已切换 Debian 源为清华镜像，并启用 apt 重试与最小化安装 ffmpeg
- 如仍卡在 apt：
  - 尝试 `docker compose build --no-cache`
  - 检查服务器 DNS/代理；必要时临时 `docker build --network host .`
  - 重试几次 `apt-get -o Acquire::Retries=3 update`

#### 容器录音说明
- 容器镜像仅支持“客户端录音”（浏览器麦克风）；不安装服务端麦克风依赖（pyaudio/sounddevice/webrtcvad），避免编译失败与体积膨胀
- 如需服务端录音，请在宿主机运行本地模式（非容器），并安装 PortAudio 与对应 Python 包

**浏览器录音权限与安全上下文**
- getUserMedia 仅在 https、localhost 或 127.0.0.1 下可用
- 远程调试可用 SSH 端口转发：
  - `ssh -f -N -i /path/to/key.pem -L 8502:localhost:8502 用户@服务器IP`
  - 经跳板：`ssh -f -N -J 跳板用户@跳板IP -i /path/to/key.pem 路由用户@目标IP -L 8502:localhost:8502`
- 公网访问建议加 HTTPS（Caddy/Nginx 或 Cloudflare Tunnel/ngrok）

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

### 5. Linux/CentOS 本机部署（不使用 Docker）
适用于需要直接运行在宿主机的场景（客户端录音仍在浏览器端进行）。
- 安装 Python 3.11（CentOS 7 建议 pyenv + openssl11-devel）
  - `yum groupinstall -y "Development Tools"`
  - `yum install -y epel-release openssl11-devel zlib-devel bzip2-devel readline-devel sqlite-devel libffi-devel xz-devel git wget`
  - `pyenv install 3.11.9 && pyenv global 3.11.9`
- 虚拟环境与依赖
  - `python -m venv venv && source venv/bin/activate`
  - `python -m pip install --upgrade pip setuptools wheel`
  - `pip install -r requirements-base.txt`
- ffmpeg（处理非 WAV）
  - `yum install -y ffmpeg`（仓库无则用静态版）
- 运行
  - `streamlit run web_app.py --server.port 8502`
  - 浏览器访问 `http://localhost:8502` 或通过 SSH 转发在本机访问

---

## ❓ 常见问题 (FAQ)

**Q: 启动 Web 界面报错 `ModuleNotFoundError`？**
A: 请确保你已经激活了虚拟环境 (`source venv/bin/activate`) 并且执行了 `pip install -r requirements.txt`。

**Q: RAG 问答搜不到内容？**
A: 向量库需要先有数据。请先使用 Web 上传录音，或者用 CLI 模式处理一些文件，系统会自动建立索引。

**Q: 实时录音报错 `Audio Hardware Not Running`？**
A: 这是 macOS 权限问题。请不要在 IDE 内置终端运行，请打开系统自带的 Terminal.app 运行命令。
