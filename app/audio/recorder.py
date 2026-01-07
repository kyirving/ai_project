import sounddevice as sd
import webrtcvad
import collections
import queue
import sys
import wave
import os
import time
import threading
import numpy as np
from app.asr.whisper_client import AudioTranscriber
from app.llm.summarizer import MeetingSummarizer
from app.utils.notifier import EmailNotifier
import app.utils.config as config

class RealtimeAssistant:
    def __init__(self, transcriber, summarizer, notifier, knowledge_base=None):
        self.transcriber = transcriber
        self.summarizer = summarizer
        self.notifier = notifier
        self.knowledge_base = knowledge_base
        
        # VAD 设置
        # sounddevice 读取的是 float32 或 int16，我们需要 int16 给 webrtcvad
        self.vad = webrtcvad.Vad(3)
        self.sample_rate = 16000 
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000) # samples per frame
        
        # 队列
        self.audio_queue = queue.Queue()
        self.is_running = False
        
        # 状态
        self.full_transcript = []
        self.temp_filename = "temp_recording.wav"

    def audio_callback(self, indata, frames, time, status):
        """
        sounddevice 的回调函数，实时获取音频数据
        """
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def stop(self):
        """
        外部调用此方法停止录音
        """
        print("🛑 正在停止录音...")
        self.is_running = False

    def run(self):
        print("\n🎙️  实时会议助手已启动")
        print("按 Ctrl+C 结束会议并生成纪要...\n")
        
        # --- 设备诊断与选择 ---
        print("--- 音频设备列表 ---")
        target_device_index = None
        target_device_name = None
        
        try:
            devices = sd.query_devices()
            print(devices)
            
            # 1. 寻找外置麦克风 (优先)
            # 遍历所有设备索引，避免迭代对象可能出现的格式问题
            device_count = len(devices)
            for i in range(device_count):
                try:
                    dev_info = sd.query_devices(i)
                    # 检查是否有输入通道
                    if dev_info.get('max_input_channels', 0) > 0 or dev_info.get('maxInputChannels', 0) > 0:
                        name = dev_info['name'].lower()
                        # 匹配常见的耳机麦克风名称
                        if "external" in name or "外置" in name or "headset" in name:
                            target_device_index = i
                            target_device_name = dev_info['name']
                            print(f"\n🎯 自动检测到耳机/外置麦克风: {target_device_name} (Index: {i})")
                            break
                except Exception:
                    continue
            
            # 2. 如果没找到外置，就用默认
            if target_device_index is None:
                default_input = sd.query_devices(kind='input')
                target_device_index = default_input['index']
                target_device_name = default_input['name']
                print(f"\n🎤 使用系统默认输入设备: {target_device_name} (Index: {target_device_index})")

            # 3. 获取目标设备的采样率
            device_info = sd.query_devices(target_device_index)
            # 兼容不同版本的属性名 (default_samplerate vs defaultSampleRate)
            hw_rate = device_info.get('default_samplerate') or device_info.get('defaultSampleRate') or 48000
            hw_rate = int(hw_rate)
            print(f"   设备原生采样率: {hw_rate} Hz")
            
            # 4. 自动适配采样率
            # VAD 支持 8000, 16000, 32000, 48000
            if hw_rate in [8000, 16000, 32000, 48000]:
                self.sample_rate = hw_rate
                print(f"✅ 完美适配: 使用设备原生采样率 {self.sample_rate} Hz")
            else:
                # 如果设备是 44100，VAD 不支持。
                # 这种情况下，我们必须用设备原生的 44100 录音，然后在内存里重采样到 16000 给 VAD 用。
                # 但为了代码简单，我们先尝试强制请求 16000，看设备是否支持重采样。
                print(f"⚠️ 设备采样率 {hw_rate} Hz 不被 VAD 直接支持。")
                print("🔄 尝试请求 16000 Hz (依赖系统重采样)...")
                self.sample_rate = 16000
                
            # 更新帧大小
            self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
            
        except Exception as e:
            print(f"⚠️ 设备查询/适配失败: {e}")
            target_device_index = None # 回退到 None (让 sounddevice 自己决定)
        print("--------------------\n")

        self.is_running = True
        
        # 语音缓冲
        speech_buffer = collections.deque(maxlen=50)
        triggered = False
        speech_frames = []
        
        silence_threshold = 20 # ~600ms
        silence_counter = 0
        min_speech_frames = 10 # 至少 ~300ms

        print(">>> 正在监听...")

        # 模拟模式检查
        simulate_mic = os.getenv("SIMULATE_MIC", "false").lower() == "true"
        stream = None
        sim_thread = None

        if simulate_mic:
            print("⚠️  使用模拟模式: 读取 data/test.wav 代替麦克风")
            if not os.path.exists("data/test.wav"):
                print("❌ 文件 data/test.wav 不存在，请放入一个音频文件用于模拟。")
                return
            
            def simulate_input():
                try:
                    with wave.open("data/test.wav", 'rb') as wf:
                        if wf.getframerate() != self.sample_rate:
                            print(f"❌ 模拟文件采样率必须是 {self.sample_rate}Hz")
                            return
                        
                        while self.is_running:
                            data = wf.readframes(self.frame_size)
                            if len(data) == 0:
                                time.sleep(1) # 播放结束
                                break
                            self.audio_queue.put(data)
                            time.sleep(self.frame_duration / 1000)
                except Exception as e:
                    print(f"模拟线程出错: {e}")

            sim_thread = threading.Thread(target=simulate_input)
            sim_thread.start()
        
        else:
            # 真实麦克风模式
            try:
                stream = sd.InputStream(samplerate=self.sample_rate, 
                                    blocksize=self.frame_size,
                                    device=target_device_index, # 使用选定的设备索引
                                    channels=1, 
                                    dtype='int16',
                                    callback=self.audio_callback)
                stream.start()
            except Exception as e:
                print(f"❌ 无法启动麦克风: {e}")
                print("💡 提示: 请尝试在外部终端运行 (source venv/bin/activate && python3 main.py)")
                print("💡 或者: 在 .env 设置 SIMULATE_MIC=true 使用文件模拟")
                self.is_running = False
                return

        # 主循环
        try:
            while self.is_running:
                try:
                    # 从队列获取音频块
                    chunk = self.audio_queue.get(timeout=1)
                    
                    # VAD 检测
                    is_speech = self.vad.is_speech(chunk, self.sample_rate)

                    if triggered:
                        speech_frames.append(chunk)
                        if not is_speech:
                            silence_counter += 1
                        else:
                            silence_counter = 0
                            
                        if silence_counter > silence_threshold:
                            triggered = False
                            # 只有当语音长度足够时才处理
                            if len(speech_frames) > min_speech_frames:
                                self._process_speech(speech_frames)
                            else:
                                print("(忽略过短的噪音)", end="\r")
                                
                            speech_frames = []
                            silence_counter = 0
                            print(">>> 正在监听...", end="\r")
                    else:
                        speech_buffer.append(chunk)
                        if is_speech:
                            triggered = True
                            speech_frames.extend(speech_buffer)
                            speech_buffer.clear()
                            print("🎤  正在说话...", end="\r")
                            
                except queue.Empty:
                    if not self.is_running:
                        break
                    continue

        except KeyboardInterrupt:
            print("\n\n🛑 会议结束。")
        except Exception as e:
            print(f"\n❌ 运行时出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            # 清理资源
            if stream:
                try:
                    stream.stop()
                    stream.close()
                except: pass
            
            if sim_thread and sim_thread.is_alive():
                sim_thread.join(timeout=1)
            
            if os.path.exists(self.temp_filename):
                try:
                    os.remove(self.temp_filename)
                except: pass
            
            self._finish_meeting()

    def _process_speech(self, frames):
        if not frames:
            return
            
        # 保存为临时 WAV 文件
        # 为了调试，我们保存一份带时间戳的文件到 debug 目录
        timestamp = time.strftime("%H%M%S")
        debug_filename = f"debug/speech_{timestamp}.wav"
        
        with wave.open(self.temp_filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            
        # 复制一份到 debug
        with open(self.temp_filename, 'rb') as f_src:
            with open(debug_filename, 'wb') as f_dst:
                f_dst.write(f_src.read())
            
        # 识别
        try:
            print(f"🎤 正在识别 (音频已保存至 {debug_filename})...")
            text = self.transcriber.transcribe(self.temp_filename, verbose=False)
            text = text.strip()
            if text:
                print(f"📝 {text}")
                self.full_transcript.append(text)
        except Exception as e:
            print(f"识别出错: {e}")

    def _finish_meeting(self):
        if not self.full_transcript:
            print("未检测到有效语音，无需生成纪要。")
            return

        full_text = "\n".join(self.full_transcript)
        
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
        transcript_path = os.path.join("output", f"realtime_{timestamp}_transcript.txt")
        os.makedirs("output", exist_ok=True)
        
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"\n📄 完整转录已保存: {transcript_path}")

        print("🧠 正在生成会议纪要...")
        try:
            summary = self.summarizer.summarize(full_text)
            summary_path = os.path.join("output", f"realtime_{timestamp}_summary.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"✅ 会议纪要已生成: {summary_path}")
            
            # 存入知识库
            if self.knowledge_base:
                try:
                    self.knowledge_base.add_meeting(
                        summary=summary,
                        transcript=full_text,
                        metadata={"source": "realtime_recording", "date": timestamp}
                    )
                except Exception as e:
                    print(f"⚠️ 存入知识库失败: {e}")
            
            if config.ENABLE_EMAIL_NOTIFICATION:
                self.notifier.send_summary(
                    subject=f"实时会议纪要 {timestamp}",
                    summary_content=summary,
                    attachment_path=summary_path
                )
        except Exception as e:
            print(f"❌ 摘要生成失败: {e}")
