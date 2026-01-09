import streamlit as st
import os
import sys
from app.rag.vector_store import MeetingKnowledgeBase
from app.llm.summarizer import MeetingSummarizer
import app.utils.config as config
if config.ASR_PROVIDER == "funasr":
    from app.asr.funasr_client import AudioTranscriber
else:
    from app.asr.whisper_client import AudioTranscriber

# 设置页面配置
st.set_page_config(page_title="DeepMeeting 智能会议助手", page_icon="🎙️", layout="wide")

# 标题
st.title("🎙️ DeepMeeting 企业级会议知识库")
st.markdown("---")

# 初始化资源 (使用缓存避免重复加载)
@st.cache_resource
def get_knowledge_base():
    return MeetingKnowledgeBase()

@st.cache_resource
def get_summarizer():
    return MeetingSummarizer(provider=config.LLM_PROVIDER)

kb = get_knowledge_base()
summarizer = get_summarizer()

import time
from streamlit_mic_recorder import mic_recorder
from app.utils.notifier import EmailNotifier

# ... (保持 imports 不变)

# 侧边栏
st.sidebar.header("功能导航")
page = st.sidebar.radio("选择功能", ["🎙️ 在线会议室", "智能问答 (RAG)", "会议记录归档", "上传新会议"])

if page == "🎙️ 在线会议室":
    st.header("🎙️ 实时智能会议室 (Web版)")
    st.info("点击下方按钮开始录音，录音结束后自动生成纪要。此模式支持手机/电脑浏览器。")
    
    # 使用 streamlit-mic-recorder 组件
    # 返回的是一个字典: {'bytes': b'...', 'sample_rate': 44100, 'sample_width': 2, 'id': '...'}
    audio = mic_recorder(
        start_prompt="🎤 开始录音",
        stop_prompt="⏹️ 停止录音",
        key='recorder'
    )
    
    if audio:
        st.success(f"录音完成！数据大小: {len(audio['bytes']) / 1024:.2f} KB")
        
        # 1. 播放录音回放
        st.audio(audio['bytes'])
        
        if st.button("🚀 开始智能分析", type="primary"):
            try:
                # 2. 保存为临时文件
                os.makedirs("data/temp", exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                temp_wav = f"data/temp/web_record_{timestamp}.wav"
                
                with open(temp_wav, "wb") as f:
                    f.write(audio['bytes'])
                st.info(f"音频已保存: {temp_wav}")
                
                # 3. 语音转文字 (ASR)
                transcriber = AudioTranscriber(model_size=config.WHISPER_MODEL_SIZE)
                with st.spinner("🎧 正在进行语音识别..."):
                    transcript = transcriber.transcribe(temp_wav)
                
                if not transcript.strip():
                    st.error("❌ 识别结果为空，请确保麦克风权限已打开且说话清晰。")
                else:
                    st.success("✅ 识别完成！")
                    with st.expander("查看逐字稿", expanded=True):
                        st.text_area("Transcript", transcript, height=200)
                    
                    # 4. 智能摘要 (LLM)
                    with st.spinner("🧠 正在生成会议纪要..."):
                        summary = summarizer.summarize(transcript)
                    
                    st.markdown("### 📝 会议纪要")
                    st.markdown(summary)
                    
                    # 5. 存入知识库
                    with st.spinner("💾 正在归档..."):
                        kb.add_meeting(
                            summary=summary,
                            transcript=transcript,
                            metadata={"source": "web_recording", "date": timestamp}
                        )
                    st.balloons()
                    st.success("🎉 已成功归档至企业知识库！")
                    
                    # 保存摘要文件
                    os.makedirs("output", exist_ok=True)
                    summary_path = os.path.join("output", f"web_{timestamp}_summary.md")
                    with open(summary_path, "w", encoding="utf-8") as f:
                        f.write(summary)
                        
            except Exception as e:
                st.error(f"处理出错: {e}")
                import traceback
                st.code(traceback.format_exc())

if page == "智能问答 (RAG)":
    st.header("💡 智能问答")
    st.info("基于历史会议记录，回答你的问题。")
    
    query = st.text_input("请输入你的问题：", placeholder="例如：上周关于产品发布的决策是什么？")
    
    if query:
        with st.spinner("正在检索并生成答案..."):
            # 1. 检索相关文档
            docs = kb.search(query, k=3)
            
            # 2. 显示检索到的片段
            with st.expander("查看参考的会议片段"):
                for i, doc in enumerate(docs):
                    st.markdown(f"**片段 {i+1}** (来源: {doc.metadata.get('source', '未知')})")
                    st.text(doc.page_content[:200] + "...")
            
            # 3. LLM 生成回答
            # 这里我们需要直接调用 summarizer 内部的 llm
            answer = kb.query_with_llm(query, summarizer.llm)
            
            st.success("🤖 AI 回答：")
            st.markdown(answer)

elif page == "会议记录归档":
    st.header("📂 历史会议记录")
    
    # 读取 output 目录下的摘要文件
    summary_dir = "./output"
    if os.path.exists(summary_dir):
        files = [f for f in os.listdir(summary_dir) if f.endswith("_summary.md")]
        for f in files:
            with st.expander(f"📄 {f}"):
                with open(os.path.join(summary_dir, f), "r") as file:
                    st.markdown(file.read())
    else:
        st.write("暂无会议记录。")

elif page == "上传新会议":
    st.header("📤 上传并处理会议录音")
    uploaded_file = st.file_uploader("选择音频文件", type=["mp3", "wav", "m4a"])
    
    if uploaded_file is not None:
        # 显示文件信息
        file_details = {"文件名": uploaded_file.name, "文件大小": f"{uploaded_file.size / 1024 / 1024:.2f} MB"}
        st.write(file_details)
        
        # 处理按钮
        if st.button("🚀 开始AI分析"):
            try:
                # 1. 保存文件到 data 目录
                save_path = os.path.join("data", uploaded_file.name)
                os.makedirs("data", exist_ok=True)
                
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"文件已保存至: {save_path}")
                
                # 2. 语音转文字 (ASR)
                transcriber = AudioTranscriber(model_size=config.WHISPER_MODEL_SIZE)
                with st.spinner("🎧 正在进行语音识别 (Whisper)... 这可能需要几分钟"):
                    transcript = transcriber.transcribe(save_path)
                
                if not transcript.strip():
                    st.error("❌ 转录失败或内容为空")
                else:
                    st.success("✅ 语音转文字完成！")
                    with st.expander("查看逐字稿"):
                        st.text_area("Transcript", transcript, height=200)
                    
                    # 3. 智能摘要 (LLM)
                    with st.spinner("🧠 正在生成会议纪要 (LLM)..."):
                        summary = summarizer.summarize(transcript)
                    
                    st.success("✅ 会议纪要生成完毕！")
                    st.markdown("### 📝 会议纪要")
                    st.markdown(summary)
                    
                    # 4. 存入知识库 (RAG)
                    with st.spinner("💾 正在存入企业知识库..."):
                        kb.add_meeting(
                            summary=summary,
                            transcript=transcript,
                            metadata={"source": uploaded_file.name, "date": "Web Upload"}
                        )
                    st.success("🎉 已归档至知识库，现在你可以通过‘智能问答’检索此会议了！")
                    
                    # 保存摘要文件到 output
                    os.makedirs("output", exist_ok=True)
                    summary_path = os.path.join("output", f"{os.path.splitext(uploaded_file.name)[0]}_summary.md")
                    with open(summary_path, "w", encoding="utf-8") as f:
                        f.write(summary)

            except Exception as e:
                st.error(f"❌ 处理过程中发生错误: {e}")
                import traceback
                st.code(traceback.format_exc())
