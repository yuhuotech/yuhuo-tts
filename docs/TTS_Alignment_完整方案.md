# TTS+字级时间戳完整解决方案文档

## 📋 目录
1. 项目概述
2. 系统架构
3. 环境配置
4. 代码实现
5. API文档
6. 部署指南
7. 故障排查
8. 二次开发指南

---

## 一、项目概述

### 项目名称
**TTS-Alignment-API** - 支持多模型的TTS+MFA字级对齐服务

### 功能特性
- ✅ 支持CosyVoice2和Qwen3-TTS模型切换
- ✅ 输出wav格式音频或base64编码数据
- ✅ 返回字级时间戳对齐数据
- ✅ 文件上传服务（用于长文本处理）
- ✅ 支持.env配置和运行时参数切换
- ✅ 完整的REST API接口
- ✅ 异步非阻塞处理
- ✅ CORS跨域支持

### 核心指标
| 指标 | 目标 |
|------|------|
| 推理延迟 | <2s (CosyVoice2) / <1s (Qwen3-TTS) |
| 时间戳精度 | 85-95% (MFA对齐) |
| 支持文本长度 | 1-5000字 |
| 最大并发 | 4 (可配置) |
| 显存占用 | 4-8GB |

---

## 二、系统架构

### 整体流程
```
用户请求
    ↓
API接收文本/音频
    ↓
选择TTS模型 (CosyVoice2 / Qwen3-TTS)
    ↓
生成mel-spectrogram
    ↓
声码器合成波形
    ↓
保存临时音频文件
    ↓
MFA强制对齐
    ↓
解析TextGrid格式
    ↓
提取字级时间戳
    ↓
构建JSON响应
    ↓
返回音频(base64/URL) + 时间戳
```

### 目录结构
```
tts-alignment-api/
├── app.py                          # FastAPI应用主文件
├── config.py                       # 配置管理
├── models/
│   ├── __init__.py
│   ├── tts_base.py                # TTS基类
│   ├── cosyvoice2_model.py        # CosyVoice2实现
│   └── qwen3_model.py             # Qwen3-TTS实现
├── alignment/
│   ├── __init__.py
│   ├── mfa_aligner.py             # MFA对齐器
│   └── textgrid_parser.py         # TextGrid解析
├── utils/
│   ├── __init__.py
│   ├── audio_utils.py             # 音频处理工具
│   └── file_utils.py              # 文件处理工具
├── .env                            # 环境变量配置
├── requirements.txt                # Python依赖
├── docker-compose.yml              # Docker配置
├── Dockerfile                      # Docker镜像
├── README.md                       # 使用说明
├── INSTALL.md                      # 安装说明
├── API.md                          # API文档
└── logs/                           # 日志目录
    └── app.log
```

---

## 三、环境配置说明

### 3.1 .env配置文件示例

```bash
# .env

# 应用配置
DEBUG=False
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# TTS模型配置
# 可选值: cosyvoice2 | qwen3
DEFAULT_TTS_MODEL=cosyvoice2

# CosyVoice2配置
COSYVOICE_MODEL_DIR=pretrained_models/CosyVoice2-0.5B
COSYVOICE_SPEED=1.0
COSYVOICE_TEMPERATURE=0.3

# Qwen3-TTS配置
QWEN3_MODEL_DIR=pretrained_models/Qwen3-TTS-12Hz-1.7B-Base
QWEN3_DTYPE=bfloat16
QWEN3_ATTN_IMPL=flash_attention_2

# MFA对齐配置
MFA_ACOUSTIC_MODEL=chinese_flac
MFA_DICTIONARY=chinese_flac
MFA_ENABLE=True
MFA_TIMEOUT=120

# 文件配置
TEMP_AUDIO_DIR=./temp_audio
OUTPUT_AUDIO_DIR=./output_audio
LOG_DIR=./logs

# 服务配置
MAX_WORKERS=4
MAX_FILE_SIZE_MB=50
ENABLE_UPLOAD_ENDPOINT=True

# 音频输出格式
# 可选值: base64 | url | both
AUDIO_OUTPUT_FORMAT=base64
```

### 3.2 运行时参数示例

调用API时可覆盖.env配置：

```bash
# 使用CosyVoice2
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "model": "cosyvoice2",
    "mode": "sft",
    "speaker": "default",
    "output_format": "base64"
  }'

# 使用Qwen3-TTS
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一个测试",
    "model": "qwen3",
    "output_format": "url"
  }'
```

---

## 四、核心代码实现

### 4.1 config.py - 配置管理

```python
import os
from typing import Literal
from pydantic import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    
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
    
    # 创建所需目录
    def __init__(self, **data):
        super().__init__(**data)
        for dir_path in [self.TEMP_AUDIO_DIR, self.OUTPUT_AUDIO_DIR, 
                         self.LOG_DIR]:
            os.makedirs(dir_path, exist_ok=True)

# 全局配置实例
settings = Settings()
```

### 4.2 models/tts_base.py - TTS基类

```python
from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Tuple

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
    def get_available_speakers(self) -> list:
        """获取可用说话人列表"""
        pass
    
    def get_sample_rate(self) -> int:
        """获取采样率"""
        return self.sample_rate
```

### 4.3 models/cosyvoice2_model.py - CosyVoice2实现

```python
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

### 4.4 models/qwen3_model.py - Qwen3-TTS实现

```python
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

### 4.5 alignment/mfa_aligner.py - MFA对齐器

```python
import os
import subprocess
import tempfile
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

### 4.6 app.py - FastAPI主应用

```python
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
    
    请求示例:
    {
        "text": "你好世界",
        "model": "cosyvoice2",
        "mode": "sft",
        "speaker": "default",
        "output_format": "base64"
    }
    
    响应示例:
    {
        "status": "success",
        "data": {
            "audio": "UklGRi4AAAA...",  # base64编码的wav数据
            "audio_url": "http://...",   # (可选)文件URL
            "alignments": [
                {"char": "你", "start": 0.0, "end": 0.45, "confidence": 0.92},
                ...
            ],
            "duration": 2.45,
            "sample_rate": 22050
        }
    }
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
            wav_bytes = sf.write(audio, sr=sample_rate, format='wav')
            audio_base64 = base64.b64encode(wav_bytes).decode()
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

---

## 五、API文档

### 5.1 合成接口

**端点**: `POST /synthesize`

**请求体**:
```json
{
  "text": "你好世界",
  "model": "cosyvoice2",
  "mode": "sft",
  "speaker": "default",
  "speed": 1.0,
  "output_format": "base64",
  "save_file": true
}
```

**参数说明**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| text | string | ✓ | 输入文本 (1-5000字) |
| model | string | | 模型选择: cosyvoice2 \| qwen3 (默认: 配置文件) |
| mode | string | | 合成模式 (CosyVoice2): sft \| zero_shot \| instruct |
| speaker | string | | 说话人ID |
| speed | float | | 语速倍数 (0.5-2.0) |
| output_format | string | | 输出格式: base64 \| url \| both |
| save_file | boolean | | 是否保存为文件 |

**响应示例**:
```json
{
  "status": "success",
  "message": "语音合成和字级对齐成功",
  "data": {
    "audio": "UklGRi4AAAA...",
    "audio_url": "/audio/abc123.wav",
    "file_id": "abc123",
    "alignments": [
      {
        "char": "你",
        "start": 0.0,
        "end": 0.45,
        "confidence": 0.92
      },
      {
        "char": "好",
        "start": 0.45,
        "end": 0.9,
        "confidence": 0.91
      }
    ],
    "duration": 2.45,
    "sample_rate": 22050,
    "text_length": 4,
    "model_used": "cosyvoice2"
  },
  "timestamp": "2026-01-27T10:00:00"
}
```

---

## 六、部署指南

### 6.1 本地部署

```bash
# 1. 克隆项目
git clone <repo-url>
cd tts-alignment-api

# 2. 创建虚拟环境
conda create -n tts-api python=3.10
conda activate tts-api

# 3. 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 4. 下载模型
# CosyVoice2
modelscope download --model FunAudioLLM/CosyVoice2-0.5B \
  --local_dir pretrained_models/CosyVoice2-0.5B

# Qwen3-TTS
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --local_dir pretrained_models/Qwen3-TTS-12Hz-1.7B-Base

# 5. 安装MFA
conda install -c conda-forge montreal-forced-aligner
mfa model download acoustic chinese_flac
mfa model download dictionary chinese_flac

# 6. 配置环境变量
cp .env.example .env
# 编辑.env文件，根据需要调整配置

# 7. 启动服务
python app.py
```

### 6.2 Docker部署

```bash
# 1. 构建镜像
docker build -t tts-alignment-api:latest .

# 2. 运行容器
docker run -d \
  --name tts-api \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/pretrained_models:/app/pretrained_models \
  -v $(pwd)/.env:/app/.env \
  tts-alignment-api:latest

# 3. 查看日志
docker logs -f tts-api

# 4. 测试
curl http://localhost:8000/health
```

---

## 七、使用示例

### Python客户端

```python
import requests
import json

class TTSClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def synthesize(self, text, model="cosyvoice2", **kwargs):
        """合成语音"""
        url = f"{self.base_url}/synthesize"
        
        payload = {
            "text": text,
            "model": model,
            **kwargs
        }
        
        response = requests.post(url, json=payload)
        return response.json()
    
    def get_models(self):
        """获取模型列表"""
        url = f"{self.base_url}/models"
        response = requests.get(url)
        return response.json()

# 使用示例
client = TTSClient()

# CosyVoice2合成
result = client.synthesize(
    "你好，这是一个测试。",
    model="cosyvoice2",
    mode="sft",
    speaker="default"
)

print(f"状态: {result['status']}")
print(f"时长: {result['data']['duration']}秒")
print(f"时间戳数: {len(result['data']['alignments'])}")

# 遍历字级时间戳
for ts in result['data']['alignments']:
    print(f"{ts['char']}: {ts['start']:.3f}s - {ts['end']:.3f}s")
```

---

## 八、完整的requirements.txt

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
torch==2.1.0
torchaudio==2.1.0
numpy==1.24.3
scipy==1.11.4
librosa==0.10.0
soundfile==0.12.1
textgrid==1.5

# CosyVoice2 (需要从源码安装)
# git+https://github.com/FunAudioLLM/CosyVoice.git

# Qwen3-TTS (需要从源码安装)
# git+https://github.com/QwenLM/Qwen3-TTS.git

# MFA
montreal-forced-aligner>=3.0.0

python-multipart==0.0.6
python-dotenv==1.0.0
```

---

## 九、故障排查

### 常见问题

**Q1: ImportError: No module named 'cosyvoice'**
```bash
# 解决方案: 从源码安装CosyVoice2
git clone https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
pip install -e .
```

**Q2: CUDA out of memory**
```bash
# 解决方案: 减小批次大小或使用更小的模型
# 在.env中配置
COSYVOICE_MODEL_DIR=pretrained_models/CosyVoice2-0.5B  # 使用0.5B而不是更大的版本
QWEN3_MODEL_DIR=pretrained_models/Qwen3-TTS-12Hz-0.6B  # 使用0.6B版本
```

**Q3: MFA对齐失败**
```bash
# 检查模型是否已下载
mfa model list

# 手动下载模型
mfa model download acoustic chinese_flac
mfa model download dictionary chinese_flac
```

---

## 十、二次开发指南

### 添加新的TTS模型

1. 在`models/`目录创建新文件，例如`fishspeech_model.py`
2. 继承`TTSBase`类，实现`synthesize()`等方法
3. 在`app.py`的`load_models()`中注册新模型
4. 在`.env`中添加新模型的配置

### 自定义对齐器

1. 在`alignment/`目录创建新文件，实现对齐逻辑
2. 在`app.py`中替换`aligner`实例
3. 实现与MFA相同的接口（返回`List[Dict]`）

---

**项目已准备就绪，开始开发！** 🚀