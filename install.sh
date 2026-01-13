#!/bin/bash
# save as install_deps.sh

echo "=== 安装基础依赖 ==="
pip install --upgrade pip
pip install numpy<2.0.0 python-dotenv requests dashscope zhipuai

echo "=== 安装LangChain相关 ==="
pip install langchain langchain-community langchain-openai langchain-ollama langchain-huggingface
pip install sentence-transformers faiss-cpu chromadb langchain-chroma

echo "=== 安装PyTorch ==="
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

echo "=== 安装音频处理 ==="
pip install pydub webrtcvad sounddevice
# pyaudio 可能有问题，先跳过或最后处理

echo "=== 安装AI模型 ==="
pip install faster-whisper
pip install modelscope "funasr==0.9.9"

echo "=== 安装应用框架 ==="
pip install streamlit streamlit-mic-recorder pyinstaller

echo "=== 安装完成 ==="