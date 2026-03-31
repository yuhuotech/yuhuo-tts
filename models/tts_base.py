"""TTS模型基类"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Tuple, List
import torch

class TTSBase(ABC):
    """TTS模型基类"""

    def __init__(self, model_id: str, device: str = "auto"):
        self.model_id = model_id
        self.device = self._resolve_device(device)
        self.sample_rate = 22050  # 默认采样率

    def _resolve_device(self, device: str) -> str:
        """解析运行设备，默认按 CUDA -> MPS -> CPU 回退。"""
        if device != "auto":
            return device
        if torch.cuda.is_available():
            return "cuda:0"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

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
