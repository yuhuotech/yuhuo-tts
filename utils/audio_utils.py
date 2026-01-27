"""音频处理工具"""

import numpy as np
import librosa
import soundfile as sf
from typing import Tuple
import warnings

warnings.filterwarnings('ignore')

def normalize_audio(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """规范化音频电平"""
    if len(audio) == 0:
        return audio
    rms = np.sqrt(np.mean(audio ** 2))
    if rms == 0:
        return audio
    current_db = 20 * np.log10(rms + 1e-10)
    gain = 10 ** ((target_db - current_db) / 20)
    normalized = audio * gain
    normalized = np.clip(normalized, -1.0, 1.0)
    return normalized.astype(np.float32)

def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """音频重采样"""
    if orig_sr == target_sr:
        return audio
    resampled = librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr, res_type='julius_fast')
    return resampled.astype(np.float32)

def get_audio_duration(audio: np.ndarray, sr: int) -> float:
    """获取音频时长 (秒)"""
    return len(audio) / sr

def get_audio_energy(audio: np.ndarray) -> float:
    """获取音频能量"""
    return float(np.sqrt(np.mean(audio ** 2)))

def apply_fade(audio: np.ndarray, sr: int, fade_in_duration: float = 0.1, fade_out_duration: float = 0.1) -> np.ndarray:
    """应用淡入淡出效果"""
    fade_in_samples = int(fade_in_duration * sr)
    fade_out_samples = int(fade_out_duration * sr)
    result = audio.copy()
    if fade_in_samples > 0 and fade_in_samples < len(result):
        result[:fade_in_samples] *= np.linspace(0, 1, fade_in_samples)
    if fade_out_samples > 0 and fade_out_samples < len(result):
        result[-fade_out_samples:] *= np.linspace(1, 0, fade_out_samples)
    return result

def enhance_audio(audio: np.ndarray, sr: int) -> np.ndarray:
    """简单的音频增强 (去噪)"""
    from scipy import signal
    sos = signal.butter(4, 80, 'hp', fs=sr, output='sos')
    enhanced = signal.sosfilt(sos, audio)
    return enhanced.astype(np.float32)
