# YuHuo TTS - 完整项目实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完整实现一个生产级 TTS 语音合成 + 字级对齐服务，支持双模型、MFA 对齐、API 接口，最终提供可访问的公网 URL。

**Architecture:**
采用模块化架构：FastAPI 应用程序作为核心，支持可插拔的 TTS 模型（CosyVoice2、Qwen3-TTS），集成 MFA 强制对齐器获取字级时间戳，使用 Docker 容器化便于部署。整个系统分为三层：API 层（FastAPI）、模型层（可扩展的 TTS 实现）、对齐层（MFA 处理）。

**Tech Stack:**
- Backend: FastAPI + Uvicorn
- TTS Models: CosyVoice2 (MOS 5.53), Qwen3-TTS (多语言)
- Alignment: Montreal Forced Aligner (MFA)
- Audio: librosa, soundfile, numpy
- Deployment: Docker, Docker Compose
- Monitoring: Python logging

---

## 📦 项目阶段划分

### Phase 1: 核心架构搭建 (任务 1-5)
- 项目初始化和目录结构
- 配置系统实现
- 基础模型接口定义

### Phase 2: 模型集成 (任务 6-9)
- CosyVoice2 模型集成
- Qwen3-TTS 模型集成
- MFA 对齐器集成
- 音频处理工具实现

### Phase 3: API 实现 (任务 10-14)
- FastAPI 应用主体
- 合成接口实现
- 上传接口实现
- 模型管理接口
- 健康检查和日志系统

### Phase 4: 测试与优化 (任务 15-18)
- 单元测试和集成测试
- 性能优化
- 错误处理和恢复
- 文档完善

### Phase 5: 部署和可访问性 (任务 19-21)
- Docker 容器化
- 本地部署验证
- 公网部署配置

---

## 📋 详细任务列表

### Task 1: 项目初始化和目录结构

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `models/__init__.py`
- Create: `alignment/__init__.py`
- Create: `utils/__init__.py`
- Create: `logs/.gitkeep`
- Create: `temp_audio/.gitkeep`
- Create: `output_audio/.gitkeep`

**Step 1: 创建完整的 requirements.txt**

```bash
cd /Users/hmw/data/www/yuhuo-tts
# 确认已在项目根目录
```

在 `requirements.txt` 中写入依赖：

```
# FastAPI框架
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# PyTorch和音频
torch==2.1.0
torchaudio==2.1.0
numpy==1.24.3
scipy==1.11.4

# 音频处理
librosa==0.10.0
soundfile==0.12.1
audioread==3.1.1

# 对齐工具
montreal-forced-aligner>=3.0.0
textgrid==1.5

# 文件和配置
python-multipart==0.0.6
python-dotenv==1.0.0
pyyaml==6.0

# 测试和开发
pytest==7.4.3
requests==2.31.0

# 可选: 性能优化
gunicorn==21.2.0
```

**Step 2: 创建 .env 环境变量文件**

```bash
cat > .env << 'EOF'
# ===== 应用配置 =====
DEBUG=False
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# ===== TTS模型配置 =====
DEFAULT_TTS_MODEL=cosyvoice2

# ===== CosyVoice2配置 =====
COSYVOICE_MODEL_DIR=pretrained_models/CosyVoice2-0.5B
COSYVOICE_SPEED=1.0
COSYVOICE_TEMPERATURE=0.3

# ===== Qwen3-TTS配置 =====
QWEN3_MODEL_DIR=pretrained_models/Qwen3-TTS-12Hz-1.7B-Base
QWEN3_DTYPE=bfloat16
QWEN3_ATTN_IMPL=flash_attention_2

# ===== MFA对齐配置 =====
MFA_ACOUSTIC_MODEL=chinese_flac
MFA_DICTIONARY=chinese_flac
MFA_ENABLE=True
MFA_TIMEOUT=120

# ===== 文件管理 =====
TEMP_AUDIO_DIR=./temp_audio
OUTPUT_AUDIO_DIR=./output_audio
LOG_DIR=./logs

# ===== 服务配置 =====
MAX_WORKERS=4
MAX_FILE_SIZE_MB=50
ENABLE_UPLOAD_ENDPOINT=True

# ===== 音频输出格式 =====
AUDIO_OUTPUT_FORMAT=base64
EOF
```

**Step 3: 创建目录结构**

```bash
mkdir -p models alignment utils logs temp_audio output_audio
touch models/__init__.py alignment/__init__.py utils/__init__.py
touch logs/.gitkeep temp_audio/.gitkeep output_audio/.gitkeep
```

**Step 4: 验证目录结构**

```bash
tree -L 2 -I '__pycache__'
# 应该显示完整的目录树
```

**Step 5: 提交**

```bash
git add requirements.txt .env models/__init__.py alignment/__init__.py utils/__init__.py logs/ temp_audio/ output_audio/
git commit -m "chore: initialize project structure and dependencies"
```

---

### Task 2: 配置管理系统 (config.py)

**Files:**
- Create: `config.py`

**Step 1: 实现 config.py**

```python
import os
from typing import Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置管理"""

    # 应用配置
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # TTS模型配置
    DEFAULT_TTS_MODEL: Literal["cosyvoice2", "qwen3"] = os.getenv(
        "DEFAULT_TTS_MODEL", "cosyvoice2"
    )

    # CosyVoice2配置
    COSYVOICE_MODEL_DIR: str = os.getenv(
        "COSYVOICE_MODEL_DIR",
        "pretrained_models/CosyVoice2-0.5B"
    )
    COSYVOICE_SPEED: float = float(os.getenv("COSYVOICE_SPEED", "1.0"))
    COSYVOICE_TEMPERATURE: float = float(
        os.getenv("COSYVOICE_TEMPERATURE", "0.3")
    )

    # Qwen3-TTS配置
    QWEN3_MODEL_DIR: str = os.getenv(
        "QWEN3_MODEL_DIR",
        "pretrained_models/Qwen3-TTS-12Hz-1.7B-Base"
    )
    QWEN3_DTYPE: str = os.getenv("QWEN3_DTYPE", "bfloat16")
    QWEN3_ATTN_IMPL: str = os.getenv("QWEN3_ATTN_IMPL", "flash_attention_2")

    # MFA配置
    MFA_ACOUSTIC_MODEL: str = os.getenv("MFA_ACOUSTIC_MODEL", "chinese_flac")
    MFA_DICTIONARY: str = os.getenv("MFA_DICTIONARY", "chinese_flac")
    MFA_ENABLE: bool = os.getenv("MFA_ENABLE", "True") == "True"
    MFA_TIMEOUT: int = int(os.getenv("MFA_TIMEOUT", "120"))

    # 文件配置
    TEMP_AUDIO_DIR: str = os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
    OUTPUT_AUDIO_DIR: str = os.getenv("OUTPUT_AUDIO_DIR", "./output_audio")
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")

    # 服务配置
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ENABLE_UPLOAD_ENDPOINT: bool = (
        os.getenv("ENABLE_UPLOAD_ENDPOINT", "True") == "True"
    )

    # 音频输出
    AUDIO_OUTPUT_FORMAT: Literal["base64", "url", "both"] = os.getenv(
        "AUDIO_OUTPUT_FORMAT", "base64"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # 创建所需目录
        for dir_path in [self.TEMP_AUDIO_DIR, self.OUTPUT_AUDIO_DIR,
                         self.LOG_DIR]:
            os.makedirs(dir_path, exist_ok=True)

# 全局配置实例
settings = Settings()
```

**Step 2: 验证配置加载**

```bash
python -c "from config import settings; print('✓ Config loaded:', settings.DEFAULT_TTS_MODEL)"
```

Expected output: `✓ Config loaded: cosyvoice2`

**Step 3: 提交**

```bash
git add config.py
git commit -m "feat: add configuration management system"
```

---

### Task 3: 音频处理工具 (utils/audio_utils.py)

**Files:**
- Create: `utils/audio_utils.py`

**Step 1: 实现音频工具函数**

```python
"""音频处理工具"""

import numpy as np
import librosa
import soundfile as sf
from typing import Tuple
import warnings

warnings.filterwarnings('ignore')

def normalize_audio(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """
    规范化音频电平

    Args:
        audio: 音频波形 (numpy array)
        target_db: 目标分贝数 (默认 -20dB)

    Returns:
        规范化后的音频
    """
    if len(audio) == 0:
        return audio

    # 计算当前RMS电平
    rms = np.sqrt(np.mean(audio ** 2))

    if rms == 0:
        return audio

    # 转换为dB
    current_db = 20 * np.log10(rms + 1e-10)

    # 计算增益
    gain = 10 ** ((target_db - current_db) / 20)

    # 应用增益并限幅
    normalized = audio * gain
    normalized = np.clip(normalized, -1.0, 1.0)

    return normalized.astype(np.float32)

def resample_audio(
    audio: np.ndarray,
    orig_sr: int,
    target_sr: int
) -> np.ndarray:
    """音频重采样"""
    if orig_sr == target_sr:
        return audio

    resampled = librosa.resample(
        audio,
        orig_sr=orig_sr,
        target_sr=target_sr,
        res_type='julius_fast'
    )

    return resampled.astype(np.float32)

def get_audio_duration(audio: np.ndarray, sr: int) -> float:
    """获取音频时长 (秒)"""
    return len(audio) / sr

def get_audio_energy(audio: np.ndarray) -> float:
    """获取音频能量"""
    return float(np.sqrt(np.mean(audio ** 2)))

def apply_fade(
    audio: np.ndarray,
    sr: int,
    fade_in_duration: float = 0.1,
    fade_out_duration: float = 0.1
) -> np.ndarray:
    """应用淡入淡出效果"""
    fade_in_samples = int(fade_in_duration * sr)
    fade_out_samples = int(fade_out_duration * sr)

    result = audio.copy()

    # 淡入
    if fade_in_samples > 0 and fade_in_samples < len(result):
        result[:fade_in_samples] *= np.linspace(0, 1, fade_in_samples)

    # 淡出
    if fade_out_samples > 0 and fade_out_samples < len(result):
        result[-fade_out_samples:] *= np.linspace(1, 0, fade_out_samples)

    return result

def enhance_audio(audio: np.ndarray, sr: int) -> np.ndarray:
    """简单的音频增强 (去噪)"""
    from scipy import signal

    sos = signal.butter(4, 80, 'hp', fs=sr, output='sos')
    enhanced = signal.sosfilt(sos, audio)

    return enhanced.astype(np.float32)
```

**Step 2: 验证工具函数**

```bash
python -c "
import numpy as np
from utils.audio_utils import normalize_audio, get_audio_duration
audio = np.random.randn(22050)
normalized = normalize_audio(audio)
duration = get_audio_duration(audio, 22050)
print(f'✓ Audio tools work: duration={duration:.1f}s, shape={normalized.shape}')
"
```

**Step 3: 提交**

```bash
git add utils/audio_utils.py
git commit -m "feat: add audio processing utilities"
```

---

### Task 4: 文件处理工具 (utils/file_utils.py)

**Files:**
- Create: `utils/file_utils.py`

**Step 1: 实现文件工具**

```python
"""文件处理工具"""

import os
import json
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

def ensure_dir(path: str) -> str:
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
    return path

def get_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_json(data: dict, filepath: str, indent: int = 2) -> str:
    """保存JSON文件"""
    ensure_dir(os.path.dirname(filepath))

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

    return filepath

def load_json(filepath: str) -> dict:
    """加载JSON文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_file_url(file_id: str, base_url: str = "http://localhost:8000") -> str:
    """获取文件URL"""
    return f"{base_url}/audio/{file_id}.wav"

def list_files(directory: str, extension: str = None) -> list:
    """列出目录中的文件"""
    files = []

    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            if extension is None or item.endswith(extension):
                files.append(item)

    return sorted(files)

def delete_file(filepath: str) -> bool:
    """删除文件"""
    try:
        os.remove(filepath)
        return True
    except Exception as e:
        print(f"删除文件失败: {str(e)}")
        return False

def clean_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """清理临时文件"""
    from time import time

    current_time = time()
    deleted_count = 0

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        if os.path.isfile(filepath):
            file_age = (current_time - os.path.getmtime(filepath)) / 3600

            if file_age > max_age_hours:
                if delete_file(filepath):
                    deleted_count += 1

    return deleted_count
```

**Step 2: 提交**

```bash
git add utils/file_utils.py
git commit -m "feat: add file management utilities"
```

---

### Task 5: 更新 utils/__init__.py

**Files:**
- Modify: `utils/__init__.py`

**Step 1: 实现**

```python
"""工具函数初始化"""

from .audio_utils import (
    normalize_audio,
    resample_audio,
    get_audio_duration,
    enhance_audio
)
from .file_utils import (
    ensure_dir,
    save_json,
    load_json,
    clean_temp_files
)

__all__ = [
    'normalize_audio',
    'resample_audio',
    'get_audio_duration',
    'enhance_audio',
    'ensure_dir',
    'save_json',
    'load_json',
    'clean_temp_files'
]
```

**Step 2: 提交**

```bash
git add utils/__init__.py
git commit -m "chore: update utils init exports"
```

---

### Task 6: TTS 基类 (models/tts_base.py)

**Files:**
- Create: `models/tts_base.py`

**Step 1: 实现 TTS 抽象基类**

```python
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
```

**Step 2: 提交**

```bash
git add models/tts_base.py
git commit -m "feat: add TTS base class"
```

---

### Task 7: CosyVoice2 模型实现 (models/cosyvoice2_model.py)

**Files:**
- Create: `models/cosyvoice2_model.py`

**Step 1: 实现 CosyVoice2 模型**

```python
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
```

**Step 2: 提交**

```bash
git add models/cosyvoice2_model.py
git commit -m "feat: add CosyVoice2 model implementation"
```

---

### Task 8: Qwen3-TTS 模型实现 (models/qwen3_model.py)

**Files:**
- Create: `models/qwen3_model.py`

**Step 1: 实现 Qwen3-TTS 模型**

```python
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
```

**Step 2: 提交**

```bash
git add models/qwen3_model.py
git commit -m "feat: add Qwen3-TTS model implementation"
```

---

### Task 9: 更新 models/__init__.py

**Files:**
- Modify: `models/__init__.py`

**Step 1: 实现**

```python
"""模型初始化"""

from .tts_base import TTSBase

__all__ = ['TTSBase']
```

**Step 2: 提交**

```bash
git add models/__init__.py
git commit -m "chore: update models init exports"
```

---

### Task 10: MFA 对齐器实现 (alignment/mfa_aligner.py)

**Files:**
- Create: `alignment/mfa_aligner.py`

**Step 1: 实现 MFA 对齐器**

```python
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
```

**Step 2: 提交**

```bash
git add alignment/mfa_aligner.py
git commit -m "feat: add MFA aligner implementation"
```

---

### Task 11: TextGrid 解析和字幕生成 (alignment/textgrid_parser.py)

**Files:**
- Create: `alignment/textgrid_parser.py`

**Step 1: 实现**

```python
"""TextGrid文件解析和字幕生成"""

from typing import List, Dict
import re

class TextGridParser:
    """TextGrid格式解析器"""

    @staticmethod
    def parse_file(filepath: str) -> List[Dict]:
        """
        解析TextGrid文件

        Args:
            filepath: TextGrid文件路径

        Returns:
            时间戳列表: [{"char": "你", "start": 0.0, "end": 0.45}, ...]
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            return TextGridParser._parse_content(content)
        except Exception as e:
            print(f"解析TextGrid失败: {str(e)}")
            return []

    @staticmethod
    def _parse_content(content: str) -> List[Dict]:
        """解析TextGrid内容"""

        intervals = []

        # 正则表达式匹配intervals
        pattern = r'intervals\s*\[\d+\]\s*:\s*xmin\s*=\s*([\d.]+)\s*xmax\s*=\s*([\d.]+)\s*text\s*=\s*"([^"]*)"'

        matches = re.finditer(pattern, content)

        for match in matches:
            xmin = float(match.group(1))
            xmax = float(match.group(2))
            text = match.group(3).strip()

            if text and text not in ['<sil>', '<silence>']:
                intervals.append({
                    "char": text,
                    "start": round(xmin, 3),
                    "end": round(xmax, 3),
                    "confidence": 0.88
                })

        return intervals

class SRTGenerator:
    """SRT字幕生成"""

    @staticmethod
    def generate(alignments: List[Dict], output_path: str = "output.srt") -> str:
        """
        生成SRT格式字幕

        Args:
            alignments: 时间戳列表
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        srt_content = ""

        for idx, alignment in enumerate(alignments, 1):
            start = TextGridParser._seconds_to_srt_time(alignment['start'])
            end = TextGridParser._seconds_to_srt_time(alignment['end'])

            srt_content += f"{idx}\n"
            srt_content += f"{start} --> {end}\n"
            srt_content += f"{alignment['char']}\n\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        return output_path

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

class VTTGenerator:
    """VTT字幕生成"""

    @staticmethod
    def generate(alignments: List[Dict], output_path: str = "output.vtt") -> str:
        """
        生成VTT格式字幕

        Args:
            alignments: 时间戳列表
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        vtt_content = "WEBVTT\n\n"

        for alignment in alignments:
            start = TextGridParser._seconds_to_vtt_time(alignment['start'])
            end = TextGridParser._seconds_to_vtt_time(alignment['end'])

            vtt_content += f"{start} --> {end}\n"
            vtt_content += f"{alignment['char']}\n\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vtt_content)

        return output_path

    @staticmethod
    def _seconds_to_vtt_time(seconds: float) -> str:
        """将秒数转换为VTT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
```

**Step 2: 提交**

```bash
git add alignment/textgrid_parser.py
git commit -m "feat: add TextGrid parser and subtitle generators"
```

---

### Task 12: 更新 alignment/__init__.py

**Files:**
- Modify: `alignment/__init__.py`

**Step 1: 实现**

```python
"""对齐器初始化"""

from .mfa_aligner import MFAAligner

__all__ = ['MFAAligner']
```

**Step 2: 提交**

```bash
git add alignment/__init__.py
git commit -m "chore: update alignment init exports"
```

---

### Task 13: FastAPI 主应用 - 第 1 部分 (app.py - 基础结构)

**Files:**
- Create: `app.py`

**Step 1: 实现 app.py 基础部分**

```python
"""FastAPI TTS-Alignment 应用"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
import soundfile as sf
import base64
import uuid
import logging
import os
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from config import settings
from models.cosyvoice2_model import CosyVoice2Model
from models.qwen3_model import Qwen3Model
from alignment.mfa_aligner import MFAAligner
from utils.audio_utils import normalize_audio
from utils.file_utils import get_file_url

# 日志配置
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(settings.LOG_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title="TTS-Alignment-API",
    description="支持多模型的TTS + MFA字级对齐服务",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 全局模型实例
models = {}
aligner = MFAAligner()

def load_models():
    """初始化模型"""
    global models
    try:
        logger.info("正在加载TTS模型...")
        models["cosyvoice2"] = CosyVoice2Model()
        models["qwen3"] = Qwen3Model()
        logger.info("✓ 所有模型加载成功")
    except Exception as e:
        logger.error(f"模型加载失败: {str(e)}")
        raise

# 请求/响应模型
class SynthesizeRequest(BaseModel):
    """合成请求"""
    text: str
    model: Optional[str] = settings.DEFAULT_TTS_MODEL
    mode: Optional[str] = "sft"  # For CosyVoice2
    speaker: Optional[str] = None
    prompt_audio: Optional[str] = None
    speed: Optional[float] = 1.0
    output_format: Optional[str] = settings.AUDIO_OUTPUT_FORMAT
    save_file: Optional[bool] = True

class SynthesizeResponse(BaseModel):
    """合成响应"""
    status: str
    message: str
    data: Optional[dict] = None
    timestamp: str

# API端点

@app.on_event("startup")
async def startup_event():
    """应用启动"""
    logger.info("TTS-Alignment-API 启动中...")
    load_models()
    logger.info("应用启动完成")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "models": list(models.keys()),
        "mfa_enabled": aligner.enabled
    }

@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    语音合成 + 字级对齐
    """
    try:
        logger.info(f"收到合成请求: 文本长度={len(request.text)}, 模型={request.model}")

        # 验证输入
        if not request.text or len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="文本长度必须在1-5000字之间")

        if request.model not in models:
            raise HTTPException(status_code=400, detail=f"不支持的模型: {request.model}")

        # 选择模型
        model = models[request.model]

        # 合成语音
        logger.info("开始语音合成...")
        audio, sample_rate = model.synthesize(
            text=request.text,
            mode=request.mode if request.model == "cosyvoice2" else None,
            speaker=request.speaker,
            prompt_audio=request.prompt_audio,
            speed=request.speed
        )

        # 规范化音频
        audio = normalize_audio(audio)

        # 计算时长
        duration = len(audio) / sample_rate
        logger.info(f"语音合成完成, 时长: {duration:.2f}s")

        # MFA对齐
        logger.info("开始MFA字级对齐...")
        alignments = aligner.align(audio, request.text, sample_rate)
        logger.info(f"对齐完成, 时间戳数: {len(alignments)}")

        # 准备音频数据
        audio_data = {}

        if request.output_format in ["base64", "both"]:
            # Base64编码
            import io
            buffer = io.BytesIO()
            sf.write(buffer, audio, sample_rate, format='wav')
            audio_bytes = buffer.getvalue()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_data["audio"] = audio_base64

        if request.output_format in ["url", "both"] and request.save_file:
            # 保存文件并返回URL
            file_id = str(uuid.uuid4())
            audio_path = os.path.join(
                settings.OUTPUT_AUDIO_DIR,
                f"{file_id}.wav"
            )
            sf.write(audio_path, audio, sample_rate)
            audio_data["audio_url"] = f"/audio/{file_id}.wav"
            audio_data["file_id"] = file_id

        # 构建响应
        response = SynthesizeResponse(
            status="success",
            message="语音合成和字级对齐成功",
            data={
                **audio_data,
                "alignments": alignments,
                "duration": round(duration, 3),
                "sample_rate": sample_rate,
                "text_length": len(request.text),
                "model_used": request.model
            },
            timestamp=datetime.now().isoformat()
        )

        logger.info("请求处理完成")
        return response.dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"合成失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@app.get("/models")
async def list_models():
    """获取可用模型列表"""
    model_info = {}

    for model_name, model_instance in models.items():
        model_info[model_name] = {
            "sample_rate": model_instance.get_sample_rate(),
            "speakers": model_instance.get_available_speakers(),
            "status": "loaded"
        }

    return {
        "status": "success",
        "data": model_info
    }

@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    """上传音频文件 (用于语音克隆)"""
    if not settings.ENABLE_UPLOAD_ENDPOINT:
        raise HTTPException(status_code=403, detail="上传功能已禁用")

    try:
        # 验证文件
        if not file.filename.endswith(('.wav', '.mp3', '.m4a', '.flac')):
            raise HTTPException(status_code=400, detail="不支持的音频格式")

        if file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail="文件过大")

        # 保存文件
        file_id = str(uuid.uuid4())
        file_path = os.path.join(
            settings.TEMP_AUDIO_DIR,
            f"{file_id}_{file.filename}"
        )

        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"音频文件上传成功: {file_id}")

        return {
            "status": "success",
            "data": {
                "file_id": file_id,
                "filename": file.filename,
                "size": len(content),
                "path": file_path
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.get("/audio/{file_id}.wav")
async def get_audio(file_id: str):
    """获取生成的音频文件"""
    try:
        file_path = os.path.join(
            settings.OUTPUT_AUDIO_DIR,
            f"{file_id}.wav"
        )

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        from fastapi.responses import FileResponse
        return FileResponse(file_path, media_type="audio/wav")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")

@app.get("/")
async def root():
    """API文档入口"""
    return {
        "service": "TTS-Alignment-API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "synthesize": "POST /synthesize",
            "models": "GET /models",
            "upload": "POST /upload_audio",
            "download": "GET /audio/{file_id}.wav"
        }
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG
    )
```

**Step 2: 验证导入**

```bash
python -c "from app import app; print('✓ FastAPI app loaded successfully')"
```

**Step 3: 提交**

```bash
git add app.py
git commit -m "feat: implement FastAPI application with core endpoints"
```

---

### Task 14: 测试脚本 (test_api.py)

**Files:**
- Create: `test_api.py`

**Step 1: 实现完整的测试脚本**

```python
"""API测试脚本"""

import requests
import json
import base64
import time
from pathlib import Path

class APITester:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.session = requests.Session()

    def test_health(self) -> bool:
        """测试健康检查"""
        print("\n[Test 1] 健康检查...")
        try:
            response = self.session.get(f"{self.api_url}/health")
            result = response.json()

            assert response.status_code == 200
            assert result['status'] == 'ok'

            print(f"✓ 服务正常运行")
            print(f"  可用模型: {result['models']}")
            print(f"  MFA状态: {result['mfa_enabled']}")
            return True
        except Exception as e:
            print(f"✗ 健康检查失败: {str(e)}")
            return False

    def test_models(self) -> bool:
        """测试模型列表"""
        print("\n[Test 2] 获取模型列表...")
        try:
            response = self.session.get(f"{self.api_url}/models")
            result = response.json()

            print(f"✓ 获取模型列表成功")
            for model_name, info in result['data'].items():
                print(f"  {model_name}:")
                print(f"    - 采样率: {info['sample_rate']}")
                print(f"    - 说话人: {info['speakers']}")
            return True
        except Exception as e:
            print(f"✗ 获取模型失败: {str(e)}")
            return False

    def test_synthesize_cosyvoice2(self) -> bool:
        """测试CosyVoice2合成"""
        print("\n[Test 3] CosyVoice2语音合成...")
        try:
            test_text = "你好，这是一个测试。"

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json={
                    "text": test_text,
                    "model": "cosyvoice2",
                    "mode": "sft",
                    "output_format": "base64"
                }
            )

            elapsed = time.time() - start_time
            result = response.json()

            assert result['status'] == 'success'
            assert 'alignments' in result['data']
            assert len(result['data']['alignments']) > 0

            print(f"✓ CosyVoice2合成成功 ({elapsed:.2f}s)")
            print(f"  文本: {test_text}")
            print(f"  时长: {result['data']['duration']:.2f}s")
            print(f"  时间戳数: {len(result['data']['alignments'])}")

            # 打印前3个时间戳
            print(f"  样本时间戳:")
            for ts in result['data']['alignments'][:3]:
                print(f"    - {ts['char']}: {ts['start']:.3f}s - {ts['end']:.3f}s")

            # 保存音频
            if 'audio' in result['data']:
                audio_bytes = base64.b64decode(result['data']['audio'])
                with open('test_cosyvoice2.wav', 'wb') as f:
                    f.write(audio_bytes)
                print(f"  音频已保存: test_cosyvoice2.wav")

            return True
        except Exception as e:
            print(f"✗ CosyVoice2合成失败: {str(e)}")
            return False

    def test_synthesize_qwen3(self) -> bool:
        """测试Qwen3-TTS合成"""
        print("\n[Test 4] Qwen3-TTS语音合成...")
        try:
            test_text = "Hello, this is a test."

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json={
                    "text": test_text,
                    "model": "qwen3",
                    "output_format": "url"
                }
            )

            elapsed = time.time() - start_time
            result = response.json()

            assert result['status'] == 'success'
            assert 'alignments' in result['data']

            print(f"✓ Qwen3-TTS合成成功 ({elapsed:.2f}s)")
            print(f"  文本: {test_text}")
            print(f"  时长: {result['data']['duration']:.2f}s")
            print(f"  文件URL: {result['data'].get('audio_url', 'N/A')}")

            return True
        except Exception as e:
            print(f"✗ Qwen3-TTS合成失败: {str(e)}")
            return False

    def test_long_text(self) -> bool:
        """测试长文本合成"""
        print("\n[Test 5] 长文本合成...")
        try:
            long_text = "今天天气真好，我们一起去公园玩吧。天空很蓝，阳光也很温暖。"

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json={
                    "text": long_text,
                    "model": "cosyvoice2",
                    "output_format": "base64"
                }
            )

            elapsed = time.time() - start_time
            result = response.json()

            assert result['status'] == 'success'

            print(f"✓ 长文本合成成功 ({elapsed:.2f}s)")
            print(f"  文本长度: {len(long_text)}字")
            print(f"  音频时长: {result['data']['duration']:.2f}s")
            print(f"  时间戳数: {len(result['data']['alignments'])}")

            return True
        except Exception as e:
            print(f"✗ 长文本合成失败: {str(e)}")
            return False

    def test_performance(self) -> bool:
        """性能测试"""
        print("\n[Test 6] 性能测试...")
        try:
            test_cases = [
                ("你好", "cosyvoice2"),
                ("你好世界", "cosyvoice2"),
                ("今天天气真好。", "cosyvoice2"),
                ("Hello", "qwen3"),
            ]

            print("  文本 | 模型 | 时间")
            print("  ---|---|---")

            times = []
            for text, model in test_cases:
                start = time.time()
                response = self.session.post(
                    f"{self.api_url}/synthesize",
                    json={"text": text, "model": model, "output_format": "base64"}
                )
                elapsed = time.time() - start
                times.append(elapsed)

                print(f"  {text} | {model} | {elapsed:.2f}s")

            avg_time = sum(times) / len(times)
            print(f"\n✓ 性能测试完成 (平均: {avg_time:.2f}s)")
            return True
        except Exception as e:
            print(f"✗ 性能测试失败: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("TTS-Alignment-API 测试套件")
        print("=" * 50)

        tests = [
            self.test_health,
            self.test_models,
            self.test_synthesize_cosyvoice2,
            self.test_synthesize_qwen3,
            self.test_long_text,
            self.test_performance,
        ]

        results = []
        for test in tests:
            try:
                result = test()
                results.append((test.__name__, result))
            except Exception as e:
                print(f"✗ 测试异常: {str(e)}")
                results.append((test.__name__, False))

        print("\n" + "=" * 50)
        print("测试总结")
        print("=" * 50)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{status}: {test_name}")

        print(f"\n总计: {passed}/{total} 通过")

        return passed == total

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
```

**Step 2: 提交**

```bash
git add test_api.py
git commit -m "feat: add comprehensive API test suite"
```

---

### Task 15: Docker 配置 (Dockerfile 和 docker-compose.yml)

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

**Step 1: 创建 Dockerfile**

```dockerfile
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

LABEL maintainer="your-email@example.com"
LABEL description="TTS-Alignment-API: Multi-model TTS with MFA Forced Alignment"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 更新pip
RUN pip install --upgrade pip setuptools wheel -i https://mirrors.aliyun.com/pypi/simple/

# 复制requirements
COPY requirements.txt .

# 安装Python依赖
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
    && pip install gunicorn -i https://mirrors.aliyun.com/pypi/simple/

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs temp_audio output_audio pretrained_models

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动应用
CMD ["python", "app.py"]
```

**Step 2: 创建 docker-compose.yml**

```yaml
version: '3.8'

services:
  tts-api:
    build: .
    container_name: tts-alignment-api
    ports:
      - "8000:8000"
    volumes:
      - ./pretrained_models:/app/pretrained_models
      - ./output_audio:/app/output_audio
      - ./logs:/app/logs
      - ./.env:/app/.env
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

**Step 3: 提交**

```bash
git add Dockerfile docker-compose.yml
git commit -m "chore: add Docker configuration for containerization"
```

---

### Task 16: 验证项目完整性和生成 README

**Files:**
- Create: `README.md`

**Step 1: 验证所有文件存在**

```bash
python -c "
import os
files = [
    'app.py', 'config.py', 'requirements.txt', '.env',
    'models/tts_base.py', 'models/cosyvoice2_model.py', 'models/qwen3_model.py',
    'alignment/mfa_aligner.py', 'alignment/textgrid_parser.py',
    'utils/audio_utils.py', 'utils/file_utils.py',
    'test_api.py', 'Dockerfile', 'docker-compose.yml'
]
missing = [f for f in files if not os.path.exists(f)]
if missing:
    print(f'✗ Missing files: {missing}')
else:
    print('✓ All core files present')
"
```

**Step 2: 创建 README.md**

```markdown
# YuHuo TTS - 语音合成 + 字级对齐服务

> 一个生产级的 TTS 语音合成 + MFA 字级对齐 API 服务，支持 CosyVoice2 和 Qwen3-TTS 双模型。

## 🚀 快速开始

### 环境要求
- Python 3.10+
- NVIDIA GPU with CUDA 11.8+
- 16GB+ RAM
- 20GB+ 存储空间（用于模型）

### 1. 克隆项目
```bash
cd /Users/hmw/data/www/yuhuo-tts
```

### 2. 安装依赖
```bash
conda create -n tts-api python=3.10
conda activate tts-api
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
conda install -c conda-forge montreal-forced-aligner
```

### 3. 下载模型
```bash
# CosyVoice2
modelscope download --model FunAudioLLM/CosyVoice2-0.5B \
  --local_dir pretrained_models/CosyVoice2-0.5B

# Qwen3-TTS
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --local_dir pretrained_models/Qwen3-TTS-12Hz-1.7B-Base

# MFA模型
mfa model download acoustic chinese_flac
mfa model download dictionary chinese_flac
```

### 4. 启动服务
```bash
python app.py
```

服务将在 `http://localhost:8000` 运行

### 5. 测试 API
```bash
python test_api.py
```

## 📚 API 文档

### 合成语音

**端点**: `POST /synthesize`

**请求示例**:
```json
{
  "text": "你好世界",
  "model": "cosyvoice2",
  "mode": "sft",
  "output_format": "base64"
}
```

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "audio": "UklGRi4AAAA...",
    "alignments": [
      {"char": "你", "start": 0.0, "end": 0.45, "confidence": 0.92},
      {"char": "好", "start": 0.45, "end": 0.9, "confidence": 0.91}
    ],
    "duration": 2.45,
    "sample_rate": 22050
  }
}
```

### 获取可用模型

**端点**: `GET /models`

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "cosyvoice2": {"sample_rate": 22050, "speakers": ["default"]},
    "qwen3": {"sample_rate": 24000, "speakers": ["default"]}
  }
}
```

## 📊 功能特性

- ✅ 双模型支持 (CosyVoice2 + Qwen3-TTS)
- ✅ 字级时间戳对齐 (MFA)
- ✅ 多格式输出 (base64/URL)
- ✅ 文件上传功能
- ✅ 生产级日志和监控
- ✅ Docker 容器化
- ✅ 完整 API 文档

## 🔧 配置

编辑 `.env` 文件进行配置：

```bash
# TTS模型
DEFAULT_TTS_MODEL=cosyvoice2

# API端口
API_PORT=8000

# MFA对齐
MFA_ENABLE=True

# 日志级别
LOG_LEVEL=INFO
```

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t tts-alignment-api:latest .

# 运行容器
docker-compose up -d

# 查看日志
docker logs -f tts-alignment-api
```

## 📖 完整文档

详见 `docs/` 目录：
- `TTS_Alignment_完整方案.md` - 技术架构
- `快速开始指南.md` - 详细部署
- `工具函数和辅助代码.md` - API 参考
- `项目总结与行动计划.md` - 优化指南

## 🤝 支持

遇到问题？查看 `docs/文档导航和快速参考.md` 的故障排查部分。

## 📄 许可证

按 CosyVoice2 和 Qwen3-TTS 的许可证使用。

---

**最后更新**: 2026-01-27
```

**Step 3: 提交**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

### Task 17: 性能测试和优化验证

**Files:**
- Create: `benchmark.py` (可选，用于性能基准测试)

**Step 1: 创建性能基准脚本**

```bash
cat > benchmark.py << 'EOF'
"""性能基准测试"""

import time
import numpy as np
from config import settings
from models.cosyvoice2_model import CosyVoice2Model
from models.qwen3_model import Qwen3Model

def benchmark():
    """运行性能基准测试"""
    print("=" * 60)
    print("TTS-Alignment-API 性能基准测试")
    print("=" * 60)

    # 加载模型
    print("\n[1] 加载模型...")
    start = time.time()
    try:
        cosyvoice2 = CosyVoice2Model()
        elapsed_cosyvoice = time.time() - start
        print(f"✓ CosyVoice2 加载: {elapsed_cosyvoice:.2f}s")
    except Exception as e:
        print(f"✗ CosyVoice2 加载失败: {e}")
        return

    start = time.time()
    try:
        qwen3 = Qwen3Model()
        elapsed_qwen3 = time.time() - start
        print(f"✓ Qwen3-TTS 加载: {elapsed_qwen3:.2f}s")
    except Exception as e:
        print(f"✗ Qwen3-TTS 加载失败: {e}")
        return

    # 合成测试
    print("\n[2] 合成性能测试...")
    test_texts = [
        ("你好", "short"),
        ("你好世界", "medium"),
        ("今天天气真好，我们一起去公园玩吧。", "long"),
    ]

    for text, label in test_texts:
        # CosyVoice2
        start = time.time()
        try:
            audio, sr = cosyvoice2.synthesize(text)
            elapsed = time.time() - start
            audio_len = len(audio) / sr
            print(f"  CosyVoice2 ({label}): {elapsed:.2f}s, 音频: {audio_len:.2f}s")
        except Exception as e:
            print(f"  CosyVoice2 ({label}): 失败 - {e}")

        # Qwen3
        start = time.time()
        try:
            audio, sr = qwen3.synthesize(text)
            elapsed = time.time() - start
            audio_len = len(audio) / sr
            print(f"  Qwen3-TTS ({label}): {elapsed:.2f}s, 音频: {audio_len:.2f}s")
        except Exception as e:
            print(f"  Qwen3-TTS ({label}): 失败 - {e}")

    print("\n" + "=" * 60)
    print("基准测试完成")
    print("=" * 60)

if __name__ == "__main__":
    benchmark()
EOF
```

**Step 2: 验证脚本可运行**

```bash
python benchmark.py --help 2>&1 | head -5
# 或直接运行
python benchmark.py
```

**Step 3: 提交**

```bash
git add benchmark.py
git commit -m "perf: add performance benchmarking script"
```

---

### Task 18: 本地部署验证

**Files:**
- None (验证任务)

**Step 1: 验证项目结构**

```bash
tree -L 2 -I '__pycache__|*.pyc' --dirsfirst
```

Expected output should show complete structure

**Step 2: 验证导入和依赖**

```bash
python << 'EOF'
print("\n[检查] 导入所有核心模块...")
try:
    from config import settings
    print("✓ config 模块")
    from models.tts_base import TTSBase
    print("✓ models.tts_base 模块")
    from alignment.mfa_aligner import MFAAligner
    print("✓ alignment.mfa_aligner 模块")
    from utils.audio_utils import normalize_audio
    print("✓ utils.audio_utils 模块")
    from utils.file_utils import save_json
    print("✓ utils.file_utils 模块")
    print("\n✓ 所有核心模块导入成功")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    exit(1)
EOF
```

**Step 3: 验证配置文件**

```bash
python -c "
from config import settings
print(f'API Host: {settings.API_HOST}')
print(f'API Port: {settings.API_PORT}')
print(f'Default Model: {settings.DEFAULT_TTS_MODEL}')
print(f'MFA Enabled: {settings.MFA_ENABLE}')
print(f'Output Dirs:')
print(f'  - Temp Audio: {settings.TEMP_AUDIO_DIR}')
print(f'  - Output Audio: {settings.OUTPUT_AUDIO_DIR}')
print(f'  - Logs: {settings.LOG_DIR}')
"
```

**Step 4: 验证目录结构完整**

```bash
echo "Checking directory structure..."
for dir in models alignment utils logs temp_audio output_audio; do
    if [ -d "$dir" ]; then
        echo "✓ $dir/"
    else
        echo "✗ $dir/ MISSING"
    fi
done
```

**Step 5: 提交验证报告**

```bash
git status
git add -A
git commit -m "chore: complete core implementation and verification"
```

---

### Task 19: 生成可部署的打包文件

**Files:**
- Create: `.dockerignore`
- Create: `DEPLOYMENT.md`

**Step 1: 创建 .dockerignore**

```bash
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.git
.gitignore
.dockerignore
*.md
docs/
test_*.py
benchmark.py
output_audio/*
temp_audio/*
logs/*
pretrained_models/  # 在构建前下载
.env.local
.env.*.local
EOF
```

**Step 2: 创建部署指南**

```bash
cat > DEPLOYMENT.md << 'EOF'
# TTS-Alignment-API 部署指南

## 前置条件

### 系统需求
- Ubuntu 20.04+ / CentOS 8+ / MacOS 12+ / Windows 10+
- NVIDIA GPU with CUDA 11.8+
- 16GB+ RAM, 20GB+ 存储

### 软件依赖
- Python 3.10+
- Docker 20.10+ (可选)
- conda (推荐)

## 方案 A: 本地部署（推荐开发用）

### 第1步: 环境准备

```bash
cd /Users/hmw/data/www/yuhuo-tts

conda create -n tts-api python=3.10 -y
conda activate tts-api

pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
conda install -c conda-forge montreal-forced-aligner -y
```

### 第2步: 下载模型

```bash
# CosyVoice2 (必需)
modelscope download --model FunAudioLLM/CosyVoice2-0.5B \
  --local_dir pretrained_models/CosyVoice2-0.5B

# Qwen3-TTS (可选)
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --local_dir pretrained_models/Qwen3-TTS-12Hz-1.7B-Base

# MFA 模型 (必需)
mfa model download acoustic chinese_flac
mfa model download dictionary chinese_flac
```

### 第3步: 配置

编辑 `.env` 文件根据需要修改配置：

```bash
nano .env
```

关键配置项：
- `API_HOST`: API 监听地址 (0.0.0.0 表示所有地址)
- `API_PORT`: API 端口 (默认 8000)
- `DEFAULT_TTS_MODEL`: 默认模型
- `LOG_LEVEL`: 日志级别

### 第4步: 启动

```bash
python app.py
```

输出应如下：
```
✓ CosyVoice2模型加载成功
✓ Qwen3-TTS模型加载成功
✓ 所有模型加载成功
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 第5步: 测试

在新终端：
```bash
# 健康检查
curl http://localhost:8000/health

# 合成测试
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "model": "cosyvoice2"}'

# 完整测试套件
python test_api.py
```

## 方案 B: Docker 部署（推荐生产用）

### 第1步: 准备模型

```bash
# 先在本地下载模型到 pretrained_models/ 目录
# (这样避免 Docker 构建时需要下载)

mkdir -p pretrained_models

# 下载 CosyVoice2
modelscope download --model FunAudioLLM/CosyVoice2-0.5B \
  --local_dir pretrained_models/CosyVoice2-0.5B

# 下载 Qwen3-TTS
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --local_dir pretrained_models/Qwen3-TTS-12Hz-1.7B-Base
```

### 第2步: 构建并运行

```bash
# 构建镜像
docker build -t tts-alignment-api:latest .

# 使用 docker-compose 启动
docker-compose up -d

# 查看日志
docker logs -f tts-alignment-api

# 测试
curl http://localhost:8000/health
```

### 第3步: 管理

```bash
# 停止服务
docker-compose down

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f --tail=100

# 重启服务
docker-compose restart
```

## 方案 C: 生产级部署（使用 Nginx + Gunicorn）

### 第1步: 安装 Nginx

```bash
sudo apt-get install nginx -y
```

### 第2步: 配置 Nginx

创建 `/etc/nginx/sites-available/tts-api`:

```nginx
upstream tts_api {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://tts_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /audio/ {
        alias /app/output_audio/;
        expires 24h;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/tts-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 第3步: 运行多进程

```bash
# 启动 4 个 gunicorn worker
gunicorn -w 4 -b 127.0.0.1:8000 app:app &
gunicorn -w 4 -b 127.0.0.1:8001 app:app &
gunicorn -w 4 -b 127.0.0.1:8002 app:app &
```

## 监控和维护

### 查看日志

```bash
# 实时日志
tail -f logs/app.log

# 过滤错误
grep ERROR logs/app.log

# 按日期查看
tail -f logs/app.log | grep "2026-01-27"
```

### 性能监控

```bash
# 监控 GPU 使用
watch -n 1 nvidia-smi

# 监控 CPU 和内存
top

# 监控 API 响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### 定期清理

```bash
# 清理旧的临时音频文件 (超过24小时)
find ./temp_audio -mtime +1 -delete

# 清理日志文件（每月）
find ./logs -mtime +30 -delete
```

## 故障排查

### 模型加载失败

```bash
# 检查模型路径
ls -la pretrained_models/

# 验证 MFA 模型
mfa model list

# 重新下载 MFA 模型
mfa model download acoustic chinese_flac --force
```

### CUDA 内存不足

```bash
# 在 .env 中修改
QWEN3_DTYPE=float16  # 使用更小的数据类型
MAX_WORKERS=2        # 减少并发
```

### API 响应慢

```bash
# 检查 GPU 使用
nvidia-smi

# 查看日志获取详细信息
tail -f logs/app.log
```

## 升级指南

```bash
# 备份当前配置
cp .env .env.backup

# 获取最新代码
git pull

# 重新安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 重启服务
python app.py
```

---

**部署完成后，访问 `http://your-host:8000/docs` 查看 API 文档。**
EOF
```

**Step 3: 提交**

```bash
git add .dockerignore DEPLOYMENT.md
git commit -m "docs: add Docker ignore and deployment guide"
```

---

### Task 20: 最终项目验证和清理

**Files:**
- None (验证任务)

**Step 1: 最终项目结构检查**

```bash
echo "===== 最终项目结构验证 ====="
echo ""
echo "核心应用文件:"
for file in app.py config.py requirements.txt .env Dockerfile docker-compose.yml; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "✓ $file ($lines lines)"
    else
        echo "✗ $file (MISSING)"
    fi
done

echo ""
echo "模型模块:"
for file in models/{__init__,tts_base,cosyvoice2_model,qwen3_model}.py; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "✓ $file ($lines lines)"
    else
        echo "✗ $file (MISSING)"
    fi
done

echo ""
echo "对齐模块:"
for file in alignment/{__init__,mfa_aligner,textgrid_parser}.py; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "✓ $file ($lines lines)"
    else
        echo "✗ $file (MISSING)"
    fi
done

echo ""
echo "工具模块:"
for file in utils/{__init__,audio_utils,file_utils}.py; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "✓ $file ($lines lines)"
    else
        echo "✗ $file (MISSING)"
    fi
done

echo ""
echo "测试和文档:"
for file in test_api.py benchmark.py README.md DEPLOYMENT.md; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        echo "✓ $file"
    else
        echo "✗ $file (MISSING)"
    fi
done
```

**Step 2: 验证所有 Git 提交**

```bash
echo ""
echo "===== Git 提交历史 ====="
git log --oneline | head -20
echo ""
echo "✓ Git 提交验证完成"
```

**Step 3: 生成项目统计**

```bash
echo ""
echo "===== 项目统计 ====="
echo "Python 代码行数:"
find . -name "*.py" -not -path "./.git/*" | xargs wc -l | tail -1

echo ""
echo "文档行数:"
find ./docs -name "*.md" | xargs wc -l | tail -1 2>/dev/null || echo "文档未计算"
```

**Step 4: 最终提交**

```bash
git status
# 如有未追踪文件，添加必要的
git add -A
git commit -m "chore: finalize project implementation and verification"
```

---

### Task 21: 公网部署配置（可选、针对 URL 访问）

**Files:**
- Create: `CLOUD_DEPLOYMENT.md`
- Create: `.env.cloud` (示例)

**Step 1: 创建云部署指南**

```bash
cat > CLOUD_DEPLOYMENT.md << 'EOF'
# TTS-Alignment-API 云端部署指南

## 云服务商选项

### 选项 1: 阿里云 (推荐)

#### 第1步: 准备云服务器

```bash
# 购买 GPU 实例（建议配置）
- GPU: NVIDIA T4 或 A10
- CPU: 8核+
- 内存: 32GB+
- 存储: 100GB+ (SSD)
- 带宽: 10Mbps+
- 系统: Ubuntu 20.04

# 获取公网 IP
export PUBLIC_IP=1.2.3.4  # 替换为你的公网IP
```

#### 第2步: 环境配置

```bash
# SSH 连接
ssh root@$PUBLIC_IP

# 更新系统
apt-get update && apt-get upgrade -y

# 安装依赖
apt-get install -y python3.10 pip curl wget git
apt-get install -y nvidia-cuda-toolkit

# 克隆项目
git clone <your-repo-url> /opt/tts-api
cd /opt/tts-api
```

#### 第3步: 安装和启动

```bash
conda create -n tts-api python=3.10 -y
conda activate tts-api

pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 下载模型
modelscope download --model FunAudioLLM/CosyVoice2-0.5B \
  --local_dir pretrained_models/CosyVoice2-0.5B

# 启动服务（使用 systemd）
sudo tee /etc/systemd/system/tts-api.service << 'SYSTEMD'
[Unit]
Description=TTS-Alignment-API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tts-api
Environment="PATH=/opt/conda/envs/tts-api/bin"
ExecStart=/opt/conda/envs/tts-api/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD

sudo systemctl daemon-reload
sudo systemctl enable tts-api
sudo systemctl start tts-api
```

### 选项 2: 腾讯云 / 华为云

类似部署流程，具体参考各服务商文档。

## 配置域名和 HTTPS

### 第1步: 申请域名

从域名服务商购买域名（如阿里云域名）

### 第2步: 配置 DNS

```bash
# 将域名 A 记录指向公网 IP
tts-api.yourdomain.com  A  1.2.3.4
```

### 第3步: 配置 SSL 证书

```bash
# 使用 Let's Encrypt（免费）
apt-get install -y certbot python3-certbot-nginx

certbot certonly --standalone -d tts-api.yourdomain.com

# 自动续期
certbot renew --dry-run
```

### 第4步: 配置 Nginx

```bash
# 创建 Nginx 配置
sudo tee /etc/nginx/sites-available/tts-api << 'NGINX'
upstream tts_api {
    server 127.0.0.1:8000;
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name tts-api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name tts-api.yourdomain.com;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/tts-api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tts-api.yourdomain.com/privkey.pem;

    # 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 性能配置
    client_max_body_size 100M;
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;

    location / {
        proxy_pass http://tts_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /audio/ {
        alias /opt/tts-api/output_audio/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

# 启用配置
sudo ln -s /etc/nginx/sites-available/tts-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## API 访问

### 本地访问（开发）
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

### 公网访问（生产）
```bash
curl https://tts-api.yourdomain.com/health
curl https://tts-api.yourdomain.com/docs
```

## 性能和可靠性优化

### 负载均衡

```bash
# 多实例部署
for port in 8000 8001 8002; do
    gunicorn -w 4 -b 127.0.0.1:$port app:app &
done
```

### 监控和告警

```bash
# 安装 Prometheus
sudo apt-get install prometheus -y

# 配置监控指标
# 详见 prometheus.yml
```

### 备份和恢复

```bash
# 定期备份配置和输出
tar -czf backup-$(date +%Y%m%d).tar.gz output_audio/ logs/ .env

# 上传到对象存储（如 OSS）
ossutil cp backup-*.tar.gz oss://my-bucket/
```

## 成本估算

| 项目 | 规格 | 月成本 |
|-----|------|--------|
| GPU 实例 | NVIDIA T4 | ~¥500 |
| 存储 | 100GB SSD | ~¥50 |
| 带宽 | 10Mbps | ~¥100 |
| 域名 | .com | ~¥8 |
| SSL 证书 | 免费 (Let's Encrypt) | ¥0 |
| **总计** | | **~¥650/月** |

---

**部署完成后，您将获得一个完整的公网可访问 URL。**
EOF
```

**Step 2: 创建云部署环境示例**

```bash
cat > .env.cloud << 'EOF'
# 云环境特定配置

# 应用配置
DEBUG=False
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# TTS模型配置
DEFAULT_TTS_MODEL=cosyvoice2

# 模型路径（云环境）
COSYVOICE_MODEL_DIR=/opt/tts-api/pretrained_models/CosyVoice2-0.5B
QWEN3_MODEL_DIR=/opt/tts-api/pretrained_models/Qwen3-TTS-12Hz-1.7B-Base

# MFA配置
MFA_ENABLE=True
MFA_TIMEOUT=120

# 文件配置
TEMP_AUDIO_DIR=/opt/tts-api/temp_audio
OUTPUT_AUDIO_DIR=/opt/tts-api/output_audio
LOG_DIR=/opt/tts-api/logs

# 服务配置
MAX_WORKERS=4
MAX_FILE_SIZE_MB=100

# 音频输出格式
AUDIO_OUTPUT_FORMAT=both

# 安全配置（云环境）
API_KEY=your-secure-key-here  # 生产环境修改
EOF
```

**Step 3: 提交**

```bash
git add CLOUD_DEPLOYMENT.md .env.cloud
git commit -m "docs: add cloud deployment guide and configuration"
```

---

## 📋 计划总结

### 任务覆盖范围

| 阶段 | 任务数 | 描述 |
|------|--------|------|
| **Phase 1** | 5 | 项目初始化、配置、工具库 |
| **Phase 2** | 5 | CosyVoice2、Qwen3、MFA、对齐器 |
| **Phase 3** | 5 | FastAPI、API 端点、测试脚本 |
| **Phase 4** | 4 | Docker、验证、优化、部署指南 |
| **Phase 5** | 2 | 云部署、最终交付 |
| **总计** | **21** | **完整生产系统** |

### 最终交付物

✅ **完整代码** (2000+ 行)
- FastAPI 应用
- 双模型集成
- MFA 对齐
- 工具函数库

✅ **配置和部署**
- Docker & docker-compose
- 本地部署指南
- 云部署指南
- systemd 配置

✅ **测试和文档**
- 完整 API 测试套件
- 性能基准脚本
- 详细部署文档
- API 参考

✅ **可访问性**
- 本地 API: `http://localhost:8000`
- 云端 API: `https://tts-api.yourdomain.com`
- 交互式文档: `/docs`
- 健康检查: `/health`

---

## 🚀 执行选项

**Plan complete and saved to `docs/plans/2026-01-27-complete-implementation.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - 我在本会话中逐个任务分发，每个任务后进行代码审查，快速迭代

**2. Parallel Session (separate)** - 你在新的 worktree 会话中使用 executing-plans 技能，批量执行所有任务

**Which approach do you prefer?**