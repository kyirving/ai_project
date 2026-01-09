import os
import sys
import app.utils.config as config
if config.ASR_PROVIDER == "funasr":
    from app.asr.funasr_client import AudioTranscriber
else:
    from app.asr.whisper_client import AudioTranscriber
from app.llm.summarizer import MeetingSummarizer
from app.utils.notifier import EmailNotifier
from app.audio.recorder import RealtimeAssistant
from app.rag.vector_store import MeetingKnowledgeBase

def main():
    """
    主程序入口。
    根据配置处理音频文件或启动实时会议助手。
    """
    # 设置目录
    # 兼容打包后的路径查找
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    input_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(base_dir, "output")
    
    # 确保目录存在
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # 检查音频文件
    # 支持常见音频格式
    audio_extensions = ('.mp3', '.wav', '.m4a', '.mp4', '.flac')
    # 简单的容错处理，防止目录不存在报错
    if os.path.exists(input_dir):
        audio_files = [f for f in os.listdir(input_dir) if f.lower().endswith(audio_extensions)]
    else:
        audio_files = []
    
    if not audio_files:
        print(f"在 {input_dir} 中未找到音频文件。请放入会议录音文件。")
        return

    # 设置 HuggingFace 镜像，解决国内下载问题
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    # 解决 OpenMP 冲突
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    
    # 临时禁用 SSL 验证 (解决网络问题)
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

    # 初始化工具
    try:
        # 初始化语音识别模型 (本地运行)
        # 尝试使用 tiny 模型以提高下载成功率
        transcriber = AudioTranscriber(model_size="tiny")
        print("语音识别模型初始化完成。")

        # 初始化摘要生成器
        summarizer = MeetingSummarizer(provider=config.LLM_PROVIDER)
        print("摘要生成器初始化完成。")

        # 初始化邮件通知器
        notifier = EmailNotifier()
        print("邮件通知器初始化完成。")
        # 初始化知识库
        knowledge_base = MeetingKnowledgeBase()
        print("知识库初始化完成。")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        print("请检查 .env 配置或依赖安装情况。")
        return

    # 根据模式选择执行路径
    if config.MODE == "realtime":
        assistant = RealtimeAssistant(transcriber, summarizer, notifier, knowledge_base)
        assistant.run()
        return

    # --- 文件处理模式 ---
    for audio_file in audio_files:
        audio_path = os.path.join(input_dir, audio_file)
        base_name = os.path.splitext(audio_file)[0]
        
        # 输出文件路径
        output_summary_path = os.path.join(output_dir, f"{base_name}_summary.md")
        output_transcript_path = os.path.join(output_dir, f"{base_name}_transcript.txt")

        print(f"\n>>> 开始处理: {audio_file}")
        
        # 1. 语音转文字
        transcript = ""
        # 如果已经存在转录文件，可以选择跳过
        if os.path.exists(output_transcript_path):
            print(f"发现已存在的转录文件: {output_transcript_path}")
            print("读取中...")
            with open(output_transcript_path, "r", encoding="utf-8") as f:
                transcript = f.read()
        else:
            try:
                # Add ASR provider information to transcribe output for better debugging and tracking
                transcript = transcriber.transcribe(audio_path, provider=config.ASR_PROVIDER)
                # 保存转录文本

                # LLM 模型分析优化生成的文本
                optimized_transcript = summarizer.optimize_transcript(transcript)
                with open(output_transcript_path, "w", encoding="utf-8") as f:
                    f.write(optimized_transcript)
                print(f"转录完成，已保存至 {output_transcript_path}")
            except Exception as e:
                print(f"文件 {audio_file} 转录失败: {e}")
                continue

        if not transcript.strip():
            print("转录内容为空，跳过摘要生成。")
            continue

        # 2. 生成摘要
        try:
            summary = summarizer.summarize(transcript)
            # 保存摘要
            with open(output_summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"会议纪要生成成功，已保存至 {output_summary_path}")
            
            # 存入知识库
            try:
                knowledge_base.add_meeting(
                    summary=summary,
                    transcript=transcript,
                    metadata={"source": audio_file, "date": "2024-01-01"} # 这里可以加更真实的日期
                )
            except Exception as e:
                print(f"⚠️ 存入知识库失败: {e}")

            # 发送邮件通知
            if config.ENABLE_EMAIL_NOTIFICATION:
                notifier.send_summary(
                    subject=f"会议纪要: {base_name}",
                    summary_content=summary,
                    attachment_path=output_summary_path
                )
        except Exception as e:
            print(f"文件 {audio_file} 摘要生成失败: {e}")

    print("\n所有任务处理完成。")

if __name__ == "__main__":
    main()
