import os
from dotenv import load_dotenv
import sys

# 加载环境变量
# 如果是打包后的环境，尝试从可执行文件目录加载
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    load_dotenv(os.path.join(base_dir, ".env"))
else:
    load_dotenv()

# 工作模式
MODE = os.getenv("MODE", "file").lower()

# LLM 配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, tongyi, glm
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# OpenAI / 兼容 API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# 通义千问 (DashScope)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# 智谱 AI (GLM)
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")

# Whisper 配置
# 本地模型大小: tiny, base, small, medium, large
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# 邮件配置
ENABLE_EMAIL_NOTIFICATION = os.getenv("ENABLE_EMAIL_NOTIFICATION", "false").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.exmail.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
# 将逗号分隔的字符串转换为列表，并去除空格
EMAIL_RECIPIENTS = [email.strip() for email in os.getenv("EMAIL_RECIPIENTS", "").split(",") if email.strip()]
