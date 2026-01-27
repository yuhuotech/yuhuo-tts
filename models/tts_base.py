"""TTS模型基类"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Tuple, List

class TTSBase(ABC):
    """TTS模型基类"""

    def __init__(self, model_id: str, device: str = "cuda:0"):
        self.model_id = model_id
        self.device = device
        self.sample_rate = 22050  # 默认采样率

    @abstractmethod
    def synthesize(
        self,
        text: str,
        **kwargs
    ) -> Tuple[np.ndarray, int]:
        """
        合成语音

        Args:
            text: 输入文本
            **kwargs: 模型特定的参数

        Returns:
            (audio_waveform, sample_rate)
        """
        pass

    @abstractmethod
    def get_available_speakers(self) -> List[str]:
        """获取可用说话人列表"""
        pass

    def get_sample_rate(self) -> int:
        """获取采样率"""
        return self.sample_rate
