import os
import sys
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

def load_environment():
    """
    简化环境变量加载：
    - 默认加载项目根目录的 .env
    - 当 APP_ENV=dev 时，额外加载 .env.development
    - 本机环境变量优先（override=False）
    """
    if load_dotenv is None:
        return
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    env_name = ".env"
    env_flag = (os.getenv("APP_EVN") or os.getenv("APP_ENV") or "").strip().lower()
    if env_flag == "dev":
        env_name = ".env.development"
    path = os.path.join(base_dir, env_name)
    if os.path.exists(path):
        load_dotenv(path, override=False)
        print(f"[config] 已加载配置文件: {path}")
    
# 初始化环境加载
load_environment()

# 工作模式
MODE = os.getenv("MODE", "file").lower()

# LLM 配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, tongyi, glm
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:1.5b")

# OpenAI / 兼容 API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# 通义千问 (DashScope)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# 智谱 AI (GLM)
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")

# ASR 引擎选择与 FunASR 配置
ASR_PROVIDER = os.getenv("ASR_PROVIDER", "whisper").lower()  # whisper 或 funasr
ASR_FUNASR_MODEL = os.getenv("ASR_FUNASR_MODEL", "paraformer-zh")
ASR_FUNASR_VAD = os.getenv("ASR_FUNASR_VAD", "fsmn-vad")
ASR_FUNASR_PUNC = os.getenv("ASR_FUNASR_PUNC", "ct-punc-zh")

# Whisper 配置
# 本地模型大小: tiny, base, small, medium, large
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# 向量模型本地路径（可选，设置后优先使用本地目录，避免联网下载）
FASTEMBED_MODEL_DIR = os.getenv("FASTEMBED_MODEL_DIR", "").strip()

# 邮件配置
ENABLE_EMAIL_NOTIFICATION = os.getenv("ENABLE_EMAIL_NOTIFICATION", "false").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.exmail.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
# 将逗号分隔的字符串转换为列表，并去除空格
EMAIL_RECIPIENTS = [email.strip() for email in os.getenv("EMAIL_RECIPIENTS", "").split(",") if email.strip()]
