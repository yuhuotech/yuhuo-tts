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
