from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi, ChatZhipuAI
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
import app.utils.config as config

class MeetingSummarizer:
    """
    使用 LangChain 和 LLM 生成会议纪要的类。
    """
    def __init__(self, provider=config.LLM_PROVIDER):
        """
        初始化总结器。
        
        :param provider: LLM 提供商 (openai, tongyi, glm, ollama)
        """
        self.llm = self._get_llm(provider)
        self.prompt = PromptTemplate(
            input_variables=["text"],
            template="""
            你是一位专业的会议助手。请分析以下会议记录并提供结构化的纪要。
            
            纪要应包含：
            1. 会议主题
            2. 关键点 (项目符号列表)
            3. 待办事项 (谁需要做什么)
            4. 达成的决议

            会议记录内容:
            {text}

            会议纪要:
            """
        )
        
    def _get_llm(self, provider):
        """
        根据配置获取 LLM 实例。
        """
        if provider == "tongyi":
            return ChatTongyi(api_key=config.DASHSCOPE_API_KEY)
        elif provider == "glm":
            return ChatZhipuAI(
                api_key=config.ZHIPUAI_API_KEY,
                model="glm-4"
            )
        elif provider == "ollama":
            # 本地 Ollama
            # 8G 内存推荐使用 qwen2:1.5b 或 gemma:2b
            model_name = "qwen2:1.5b" 
            print(f"使用本地 Ollama 模型 ({model_name})...")
            return ChatOllama(model=model_name)
        else:
            # 默认为 OpenAI 或 兼容 API
            return ChatOpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL,
                model="gpt-3.5-turbo", 
                temperature=0.3
            )

    def summarize(self, text):
        """
        生成摘要。
        """
        print("正在生成会议纪要...")
        final_prompt = self.prompt.format(text=text)
        response = self.llm.invoke(final_prompt)
        return response.content
