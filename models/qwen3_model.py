"""Qwen3-TTS模型实现"""

import torch
import numpy as np
from typing import Tuple, Optional, List
from config import settings
from .tts_base import TTSBase

class Qwen3Model(TTSBase):
    """Qwen3-TTS模型"""

    def __init__(self):
        super().__init__("qwen3", device="cuda:0")
        self.sample_rate = 24000  # Qwen3-TTS的采样率
        self._load_model()

    def _load_model(self):
        """加载Qwen3-TTS模型"""
        try:
            from qwen_tts.pipeline import QwenTTSPipeline

            # 转换dtype
            dtype_map = {
                "bfloat16": torch.bfloat16,
                "float32": torch.float32,
                "float16": torch.float16
            }
            dtype = dtype_map.get(settings.QWEN3_DTYPE, torch.bfloat16)

            self.pipeline = QwenTTSPipeline(
                model_id=settings.QWEN3_MODEL_DIR,
                device=self.device,
                dtype=dtype,
                attn_implementation=settings.QWEN3_ATTN_IMPL
            )
            print("✓ Qwen3-TTS模型加载成功")
        except Exception as e:
            raise RuntimeError(f"Qwen3-TTS模型加载失败: {str(e)}")

    def synthesize(
        self,
        text: str,
        language: str = "Chinese",
        speed: float = 1.0,
        **kwargs
    ) -> Tuple[np.ndarray, int]:
        """
        使用Qwen3-TTS合成语音

        Args:
            text: 输入文本
            language: 语言 ("Chinese" | "English" | ...)
            speed: 语速倍数

        Returns:
            (audio_waveform, sample_rate)
        """
        try:
            with torch.no_grad():
                audio = self.pipeline.run(
                    text=text,
                    language=language,
                    speed=speed
                )

            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()

            audio = np.asarray(audio).flatten()

            return audio, self.sample_rate

        except Exception as e:
            raise RuntimeError(f"Qwen3-TTS合成失败: {str(e)}")

    def get_available_speakers(self) -> List[str]:
        """Qwen3-TTS不支持多说话人"""
        return ["default"]
