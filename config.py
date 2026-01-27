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
