"""CosyVoice2 TTS模型实现"""

import torch
import numpy as np
import os
from typing import Tuple, Optional, List
from config import settings
from .tts_base import TTSBase

class CosyVoice2Model(TTSBase):
    """CosyVoice2 TTS模型"""

    def __init__(self):
        super().__init__("cosyvoice2", device="cuda:0")
        self.sample_rate = 22050  # CosyVoice2的采样率
        self._load_model()

    def _load_model(self):
        """加载CosyVoice2模型"""
        try:
            from cosyvoice.cli.cosyvoice import AutoModel

            model_dir = os.path.abspath(settings.COSYVOICE_MODEL_DIR)
            self.model = AutoModel(model_dir=model_dir)
            self.sample_rate = self.model.sample_rate
            print("✓ CosyVoice2模型加载成功")
        except Exception as e:
            raise RuntimeError(f"CosyVoice2模型加载失败: {str(e)}")

    def synthesize(
        self,
        text: str,
        mode: str = "sft",
        speaker: Optional[str] = None,
        prompt_audio: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> Tuple[np.ndarray, int]:
        """
        使用CosyVoice2合成语音

        Args:
            text: 输入文本
            mode: 合成模式 ("sft" | "zero_shot" | "instruct")
            speaker: 说话人ID (SFT模式)
            prompt_audio: 参考音频路径 (zero_shot/instruct模式)
            speed: 语速倍数

        Returns:
            (audio_waveform, sample_rate)
        """
        try:
            if mode == "sft":
                # SFT模式 - 预定义说话人
                speaker = speaker or "default"
                output = self.model.inference_sft(
                    text=text,
                    spk_id=speaker,
                    stream=False,
                    speed=speed
                )

            elif mode == "zero_shot":
                # 零样本克隆模式
                prompt_text = kwargs.get("prompt_text", text)
                output = self.model.inference_zero_shot(
                    text=text,
                    prompt_text=prompt_text,
                    prompt_audio=prompt_audio,
                    stream=False
                )

            elif mode == "instruct":
                # 指令模式
                instruction = kwargs.get("instruction", "")
                output = self.model.inference_instruct2(
                    text=text,
                    instruct_text=instruction,
                    prompt_audio=prompt_audio,
                    stream=False
                )

            else:
                raise ValueError(f"不支持的模式: {mode}")

            # 提取音频数据
            if isinstance(output, dict) and "tts_speech" in output:
                audio = output["tts_speech"]
            elif isinstance(output, list) and len(output) > 0:
                # 如果是列表，取第一个元素的tts_speech
                audio = output[0].get("tts_speech") if isinstance(output[0], dict) else output[0]
            else:
                audio = output

            # 转换为 numpy 数组
            if hasattr(audio, "numpy"):
                audio = audio.numpy()

            audio = np.asarray(audio)
            if audio.ndim > 1:
                audio = audio.flatten()

            return audio, self.sample_rate

        except Exception as e:
            raise RuntimeError(f"CosyVoice2合成失败: {str(e)}")

    def get_available_speakers(self) -> List[str]:
        """获取可用说话人列表"""
        try:
            # CosyVoice2 的默认说话人列表
            if hasattr(self.model, "list_available_spks"):
                speakers = self.model.list_available_spks()
                return speakers if speakers else ["default"]
            else:
                return ["default"]
        except:
            return ["default"]
