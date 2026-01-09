import os
from funasr import AutoModel

class AudioTranscriber:
    """
    使用 FunASR Paraformer 的中文语音识别器，支持 VAD 与标点恢复。
    """
    def __init__(self, model="paraformer-zh", vad_model="fsmn-vad", punctuation_model="ct-punc-zh"):
        """
        初始化 FunASR 组件。
        
        :param model: 主 ASR 模型（中文），默认 paraformer-zh
        :param vad_model: 端点检测模型（VAD），默认 fsmn-vad
        :param punctuation_model: 标点恢复模型，默认 ct-punc-zh
        """
        try:
            self.model = AutoModel(
                model=model,
                vad_model=vad_model,
                punctuation_model=punctuation_model
            )
        except Exception as e:
            raise RuntimeError(f"FunASR 初始化失败或未安装: {e}")

    def transcribe(self, audio_path, verbose=True):
        """
        使用 FunASR 转录音频文件。
        
        :param audio_path: 音频文件路径
        :param verbose: 是否打印日志
        :return: 转录后的中文文本
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"找不到音频文件: {audio_path}")
        if verbose:
            print(f"正在转录: {audio_path}...")
        result = self.model.generate(input=audio_path, batch_size=1)
        if not result:
            return ""
        text = result[0].get("text", "")
        return text.strip()
