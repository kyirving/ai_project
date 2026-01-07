## 目标
- 生成一个可直接使用的 docker-compose.yml，包含：
  - app（DeepMeeting Web 应用，端口 8502）
  - 可选 ollama（本地 LLM，端口 11434），app 通过 http://ollama:11434 访问
- 挂载本地数据卷，确保 data/ 与 output/ 持久化
- 支持从 .env 注入环境变量（不把敏感信息写进 compose）

## docker-compose.yml（候选内容）
```yaml
version: "3.9"

services:
  app:
    build: .
    container_name: deepmeeting-app
    ports:
      - "8502:8502"
    volumes:
      - ./data:/app/data
      - ./output:/app/output
    env_file:
      - .env
    environment:
      # 如 .env 未提供时的兜底值
      LLM_PROVIDER: ${LLM_PROVIDER:-ollama}
      WHISPER_MODEL_SIZE: ${WHISPER_MODEL_SIZE:-base}
      ENABLE_EMAIL_NOTIFICATION: ${ENABLE_EMAIL_NOTIFICATION:-false}
      HF_ENDPOINT: ${HF_ENDPOINT:-}
      ASR_BACKEND: ${ASR_BACKEND:-faster_whisper}
    command: [ "streamlit", "run", "web_app.py", "--server.port", "8502", "--server.headless", "true", "--server.fileWatcherType", "none" ]
    depends_on:
      ollama:
        condition: service_started
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: deepmeeting-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 3s
      retries: 12

volumes:
  ollama:
```

## 说明
- app：
  - 使用项目根目录 Dockerfile 构建镜像（基于 python:3.11-slim + ffmpeg）
  - 端口映射 8502，访问 http://服务器IP:8502
  - 挂载 ./data 与 ./output，保持数据与向量库持久化
  - 通过 .env 注入配置；支持 ASR_BACKEND=faster_whisper / openai_whisper / whisper_cpp 的切换
- ollama：
  - 可选服务；如你使用远程 LLM 或 OpenAI/Tongyi，可将 app 的 LLM_PROVIDER 改为对应值并移除该服务
- HTTPS：如需要浏览器麦克风在公网域名下工作，我可追加 Caddy/Nginx 服务反代到 app:8502 并自动签发证书

## 使用步骤
- 构建：`docker compose build`
- 启动：`docker compose up -d`
- 首次拉取模型（如用 ollama）：`docker exec -it deepmeeting-ollama ollama run qwen2:7b`
- 访问：`http://服务器IP:8502`

## 你需确认
- 是否保留 ollama 服务；若不用本地 LLM，我可移除它并改为 OpenAI/Tongyi 配置
- 是否需要我添加 HTTPS 反向代理服务（Caddy/Nginx）
- 数据卷路径是否保持默认 ./data 与 ./output（可改为你指定的宿主机路径）

确认后，我将：
- 在仓库根生成 docker-compose.yml（上述内容）
- 如果选择 HTTPS，我会同时生成 Caddy/Nginx 配置文件
- 更新 README 添加 Docker 部署与使用说明