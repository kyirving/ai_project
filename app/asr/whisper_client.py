import os
from faster_whisper import WhisperModel

class AudioTranscriber:
    """
    使用 faster-whisper 的本地语音识别器。
    """
    def __init__(self, model_size="base"):
        """
        初始化 Whisper 模型。
        
        :param model_size: 模型大小 (tiny, base, small, medium, large-v2, large-v3)
        """
        try:
            self.model = WhisperModel(model_size, device="cpu", compute_type="float32")
        except Exception as e:
            raise RuntimeError(f"Whisper 初始化失败或未安装: {e}")

    def transcribe(self, audio_path, verbose=True):
        """
        使用 Whisper 转录音频文件。
        
        :param audio_path: 音频文件路径
        :param verbose: 是否打印日志
        :return: 转录后的文本
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"找不到音频文件: {audio_path}")
        
        if verbose:
            print(f"正在转录: {audio_path}...")
        
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5,
            language="zh",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            condition_on_previous_text=False,
            word_timestamps=True
        )
        if verbose:
            print(f"检测到语言: {info.language} (置信度: {info.language_probability:.2f})")
            print(f"音频时长: {info.duration:.2f}s")
        transcript_parts = [seg.text for seg in segments]
        return "".join(transcript_parts)
