"""CosyVoice2 TTS模型实现"""

import torch
import numpy as np
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
            from cosyvoice.cli.cosyvoice import CosyVoice2

            self.model = CosyVoice2(
                model_id_or_path=settings.COSYVOICE_MODEL_DIR,
                load_jit=False,
                load_trt=False,
                fp16=False
            )
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
                result = self.model.inference_sft(
                    text=text,
                    spk_id=speaker,
                    stream=False,
                    speed=speed
                )

            elif mode == "zero_shot":
                # 零样本克隆模式
                from cosyvoice.utils.file_utils import load_wav

                prompt_speech = load_wav(prompt_audio, 16000)
                result = self.model.inference_zero_shot(
                    text=text,
                    prompt_text=kwargs.get("prompt_text", text),
                    prompt_speech=prompt_speech,
                    stream=False,
                    speed=speed
                )

            elif mode == "instruct":
                # 指令模式
                from cosyvoice.utils.file_utils import load_wav

                prompt_speech = load_wav(prompt_audio, 16000)
                result = self.model.inference_instruct2(
                    text=text,
                    instruct_text=kwargs.get("instruct_text", ""),
                    prompt_speech=prompt_speech,
                    stream=False,
                    speed=speed
                )

            else:
                raise ValueError(f"不支持的模式: {mode}")

            # 合并音频块
            audio_list = []
            for chunk in result:
                if "tts_speech" in chunk:
                    audio_list.append(chunk["tts_speech"].numpy())

            if not audio_list:
                raise RuntimeError("TTS生成失败")

            audio = np.concatenate(audio_list, axis=1)
            audio = audio.flatten()

            return audio, self.sample_rate

        except Exception as e:
            raise RuntimeError(f"CosyVoice2合成失败: {str(e)}")

    def get_available_speakers(self) -> List[str]:
        """获取可用说话人列表"""
        try:
            speakers = self.model.list_available_spks()
            return speakers if speakers else ["default"]
        except:
            return ["default"]
