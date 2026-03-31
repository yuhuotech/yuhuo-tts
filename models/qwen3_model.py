"""Qwen3-TTS模型实现"""

from typing import List, Optional, Tuple

import numpy as np
import torch

from config import settings
from .tts_base import TTSBase


class Qwen3Model(TTSBase):
    """Qwen3-TTS Base 模型封装。"""

    def __init__(self):
        super().__init__("qwen3")
        self.sample_rate = 24000
        self._load_model()

    def _resolve_dtype(self) -> torch.dtype:
        if self.device in {"cpu", "mps"}:
            return torch.float32

        dtype_map = {
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
            "float16": torch.float16,
        }
        return dtype_map.get(settings.QWEN3_DTYPE, torch.bfloat16)

    def _resolve_attn_impl(self) -> str:
        if self.device in {"cpu", "mps"}:
            return "eager"
        return settings.QWEN3_ATTN_IMPL

    def _normalize_language(self, language: Optional[str]) -> str:
        if not language:
            return "Auto"
        normalized = language.strip()
        return normalized[:1].upper() + normalized[1:].lower()

    def _load_model(self):
        """加载Qwen3-TTS模型"""
        try:
            from qwen_tts import Qwen3TTSModel

            self.pipeline = Qwen3TTSModel.from_pretrained(
                settings.QWEN3_MODEL_DIR,
                device_map=self.device,
                dtype=self._resolve_dtype(),
                attn_implementation=self._resolve_attn_impl(),
            )
            self.sample_rate = int(getattr(self.pipeline.model, "speaker_encoder_sample_rate", 24000))
        except Exception as e:
            raise RuntimeError(f"Qwen3-TTS模型加载失败: {str(e)}")

    def synthesize(
        self,
        text: str,
        language: str = "Auto",
        prompt_audio: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> Tuple[np.ndarray, int]:
        """
        使用Qwen3-TTS Base模型进行音色克隆合成。

        当前仓库集成的是 Base 模型，要求提供参考音频。
        """
        try:
            if not prompt_audio:
                raise ValueError("Qwen3-TTS Base 模型需要提供 prompt_audio 或 uploaded_audio_id")

            normalized_language = self._normalize_language(language)
            prompt_text = kwargs.get("prompt_text")
            x_vector_only_mode = not bool(prompt_text)

            with torch.inference_mode():
                wavs, sample_rate = self.pipeline.generate_voice_clone(
                    text=text,
                    language=normalized_language,
                    ref_audio=prompt_audio,
                    ref_text=prompt_text,
                    x_vector_only_mode=x_vector_only_mode,
                )

            audio = np.asarray(wavs[0]).flatten()
            return audio, int(sample_rate)
        except Exception as e:
            raise RuntimeError(f"Qwen3-TTS合成失败: {str(e)}")

    def get_available_speakers(self) -> List[str]:
        """Base 模型不提供固定说话人列表。"""
        speakers = self.pipeline.get_supported_speakers()
        if speakers:
            return speakers
        return ["voice_clone"]
