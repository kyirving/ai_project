from faster_whisper import WhisperModel
import os
import torch

class AudioTranscriber:
    """
    使用 faster-whisper 进行本地高效语音识别的类。
    """
    def __init__(self, model_size="base"):
        """
        初始化 Whisper 模型。
        
        :param model_size: 模型大小 (tiny, base, small, medium, large-v2, large-v3)
        """
        # 初始化模型
        # device="auto" 会自动选择 cpu 或 cuda
        # compute_type="int8" 可以量化模型减少内存，"float16" 或 "float32" 精度更高
        try:
            print(f"正在加载本地 Whisper 模型 (faster-whisper): {model_size}...")
            self.model = WhisperModel(model_size, device="cpu", compute_type="float32")
            print("✅ 模型加载完成")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise

    def transcribe(self, audio_path, verbose=True):
        """
        转录音频文件。
        
        :param audio_path: 音频文件路径
        :param verbose: 是否打印日志
        :return: 转录后的文本
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"找不到音频文件: {audio_path}")
        
        if verbose:
            print(f"正在转录: {audio_path}...")
            
        # faster-whisper 返回的是 segments 生成器
        # 开启 VAD 过滤，防止静音片段导致的重复和幻觉
        # condition_on_previous_text=False: 防止在长静音后重复上一段内容
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5,
            vad_filter=True,                # 开启 VAD
            vad_parameters=dict(min_silence_duration_ms=500), # 调整 VAD 敏感度
            condition_on_previous_text=False, # 减少复读
            word_timestamps=True            # 提高准确性
        )
        
        if verbose:
            print(f"检测到语言: {info.language} (置信度: {info.language_probability:.2f})")
            print(f"音频时长: {info.duration:.2f}s")

        # 收集所有片段的文本
        transcript_parts = []
        for segment in segments:
            # 可以在这里实时打印进度
            # if verbose:
            #    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            transcript_parts.append(segment.text)
            
        return "".join(transcript_parts)
