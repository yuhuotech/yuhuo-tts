"""Montreal Forced Aligner - 字级对齐"""

import os
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import soundfile as sf
from config import settings

class MFAAligner:
    """Montreal Forced Aligner - 字级对齐"""

    def __init__(self):
        self.acoustic_model = settings.MFA_ACOUSTIC_MODEL
        self.dictionary = settings.MFA_DICTIONARY
        self.temp_dir = settings.TEMP_AUDIO_DIR
        self.enabled = settings.MFA_ENABLE

    def align(
        self,
        audio: np.ndarray,
        text: str,
        sample_rate: int
    ) -> List[Dict]:
        """
        对齐文本和音频

        Args:
            audio: 音频波形
            text: 文本
            sample_rate: 采样率

        Returns:
            [{"char": "你", "start": 0.0, "end": 0.45, "confidence": 0.92}, ...]
        """
        if not self.enabled:
            return self._fallback_alignment(text, len(audio) / sample_rate)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # 保存音频和文本
                audio_path = os.path.join(tmpdir, "audio.wav")
                text_path = os.path.join(tmpdir, "audio.lab")
                output_dir = os.path.join(tmpdir, "output")

                sf.write(audio_path, audio, sample_rate)

                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                # 运行MFA
                result = subprocess.run([
                    "mfa", "align",
                    tmpdir,
                    self.dictionary,
                    self.acoustic_model,
                    output_dir,
                    "--overwrite",
                    "--single_speaker"
                ], capture_output=True, text=True, timeout=settings.MFA_TIMEOUT)

                if result.returncode != 0:
                    print(f"MFA警告: {result.stderr}")
                    return self._fallback_alignment(text, len(audio) / sample_rate)

                # 解析TextGrid
                return self._parse_textgrid(
                    os.path.join(output_dir, "audio.TextGrid")
                )

        except Exception as e:
            print(f"MFA对齐失败: {str(e)}, 使用降级方案")
            return self._fallback_alignment(text, len(audio) / sample_rate)

    def _parse_textgrid(self, textgrid_path: str) -> List[Dict]:
        """解析TextGrid文件"""
        try:
            from textgrid import TextGrid
        except ImportError:
            print("警告: textgrid库未安装，使用降级方案")
            return []

        try:
            tg = TextGrid.fromFile(textgrid_path)
            alignments = []

            for tier in tg.tiers:
                if 'word' in tier.name.lower():
                    for interval in tier.intervals:
                        mark = interval.mark.strip()
                        if mark and mark not in ['<sil>', '<silence>']:
                            alignments.append({
                                "char": mark,
                                "start": round(interval.minTime, 3),
                                "end": round(interval.maxTime, 3),
                                "confidence": 0.88
                            })

            return alignments

        except Exception as e:
            print(f"TextGrid解析失败: {str(e)}")
            return []

    def _fallback_alignment(
        self,
        text: str,
        duration: float
    ) -> List[Dict]:
        """
        降级方案: 均匀分配时间
        """
        chars = list(text)
        num_chars = len(chars)

        if num_chars == 0:
            return []

        char_duration = duration / num_chars
        alignments = []

        for i, char in enumerate(chars):
            start = i * char_duration
            end = (i + 1) * char_duration

            alignments.append({
                "char": char,
                "start": round(start, 3),
                "end": round(end, 3),
                "confidence": 0.50  # 降级方案的低置信度
            })

        return alignments
