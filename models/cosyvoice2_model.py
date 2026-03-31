"""CosyVoice2 TTS模型实现"""

import torch
import numpy as np
import os
import sys
from typing import Tuple, Optional, List
from config import settings
from .tts_base import TTSBase

class CosyVoice2Model(TTSBase):
    """CosyVoice2 TTS模型"""

    def __init__(self):
        super().__init__("cosyvoice2")
        self.sample_rate = 22050  # CosyVoice2的采样率
        self._load_model()

    def _load_model(self):
        """加载CosyVoice2模型"""
        try:
            # 设置 PYTHONPATH（关键！）- 必须在导入之前
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            matcha_path = os.path.join(project_root, "third_party", "CosyVoice", "third_party", "Matcha-TTS")

            if os.path.exists(matcha_path) and matcha_path not in sys.path:
                sys.path.insert(0, matcha_path)

            # 也添加 CosyVoice 项目根目录
            cosyvoice_root = os.path.join(project_root, "third_party", "CosyVoice")
            if os.path.exists(cosyvoice_root) and cosyvoice_root not in sys.path:
                sys.path.insert(0, cosyvoice_root)

            # 导入 CosyVoice 官方自动选择入口，避免 CosyVoice2 模型被当作 CosyVoice1 加载
            from cosyvoice.cli.cosyvoice import AutoModel

            model_dir = os.path.abspath(settings.COSYVOICE_MODEL_DIR)
            self.model = AutoModel(model_dir=model_dir)
            self.sample_rate = getattr(self.model, "sample_rate", 22050)
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
            mode: 合成模式 ("sft" | "zero_shot" | "cross_lingual" | "instruct")
            speaker: 说话人ID (SFT/Instruct模式)
            prompt_audio: 参考音频路径 (zero_shot/cross_lingual/instruct模式)
            speed: 语速倍数 (0.5-2.0)

        Returns:
            (audio_waveform, sample_rate)
        """
        try:
            audio_list = []

            if mode == "sft":
                # SFT 模式 - 使用预训练音色
                spk_id = speaker or "中文女"
                for audio_chunk in self.model.inference_sft(
                    tts_text=text,
                    spk_id=spk_id,
                    stream=False
                ):
                    if "tts_speech" in audio_chunk:
                        audio_list.append(audio_chunk["tts_speech"])

            elif mode == "zero_shot":
                # Zero-shot 克隆模式 - 从参考音频克隆音色
                if not prompt_audio:
                    raise ValueError("zero_shot 模式需要提供 prompt_audio")

                prompt_text = kwargs.get("prompt_text", text)
                for audio_chunk in self.model.inference_zero_shot(
                    tts_text=text,
                    prompt_text=prompt_text,
                    prompt_wav=prompt_audio,
                    stream=False
                ):
                    if "tts_speech" in audio_chunk:
                        audio_list.append(audio_chunk["tts_speech"])

            elif mode == "cross_lingual":
                # 跨语言克隆模式
                if not prompt_audio:
                    raise ValueError("cross_lingual 模式需要提供 prompt_audio")

                for audio_chunk in self.model.inference_cross_lingual(
                    tts_text=text,
                    prompt_wav=prompt_audio,
                    stream=False
                ):
                    if "tts_speech" in audio_chunk:
                        audio_list.append(audio_chunk["tts_speech"])

            elif mode == "instruct":
                # Instruct 模式 - 情感/风格控制
                spk_id = speaker or "中文女"
                instruct_text = kwargs.get("instruct_text", "")

                infer_method = getattr(self.model, "inference_instruct2", None)
                if infer_method is not None and prompt_audio:
                    iterator = infer_method(
                        tts_text=text,
                        instruct_text=instruct_text,
                        prompt_wav=prompt_audio,
                        stream=False
                    )
                else:
                    iterator = self.model.inference_instruct(
                        tts_text=text,
                        spk_id=spk_id,
                        instruct_text=instruct_text,
                        stream=False
                    )

                for audio_chunk in iterator:
                    if "tts_speech" in audio_chunk:
                        audio_list.append(audio_chunk["tts_speech"])

            else:
                raise ValueError(f"不支持的模式: {mode}")

            if not audio_list:
                raise RuntimeError("TTS生成失败，未获得音频数据")

            # 合并所有音频块
            audio_tensors = audio_list
            if len(audio_tensors) > 1:
                # 在时间维度上连接
                audio = torch.cat(audio_tensors, dim=-1)
            else:
                audio = audio_tensors[0]

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
            # 获取可用音色列表（注意方法名拼写）
            if hasattr(self.model, "list_avaliable_spks"):
                speakers = self.model.list_avaliable_spks()
                return speakers if speakers else []
            elif hasattr(self.model, "list_available_spks"):
                speakers = self.model.list_available_spks()
                return speakers if speakers else []
            else:
                # 默认音色列表
                return ["中文女", "中文男"]
        except:
            return ["中文女", "中文男"]
