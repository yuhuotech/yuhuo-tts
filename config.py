from typing import Literal
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置管理"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用配置
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = False

    # TTS模型配置
    DEFAULT_TTS_MODEL: Literal["cosyvoice2", "qwen3"] = "cosyvoice2"

    # CosyVoice2配置
    COSYVOICE_MODEL_DIR: str = "./models/CosyVoice2-0.5B"
    COSYVOICE_SPEED: float = 1.0
    COSYVOICE_TEMPERATURE: float = 0.3

    # Qwen3-TTS配置
    QWEN3_MODEL_DIR: str = "./models/Qwen3-TTS-12Hz-1.7B-Base"
    QWEN3_DTYPE: str = "bfloat16"
    QWEN3_ATTN_IMPL: str = "flash_attention_2"

    # MFA配置
    MFA_ACOUSTIC_MODEL: str = "mandarin_mfa"
    MFA_DICTIONARY: str = "mandarin_mfa"
    MFA_COMMAND: str = "mfa"
    MFA_ENABLE: bool = True
    MFA_TIMEOUT: int = 120
    MFA_FALLBACK_ALIGNMENT: Literal["none", "uniform"] = "none"

    # 文件配置
    TEMP_AUDIO_DIR: str = "./temp_audio"
    OUTPUT_AUDIO_DIR: str = "./output_audio"
    LOG_DIR: str = "./logs"

    # 服务配置
    MAX_WORKERS: int = 4
    MAX_FILE_SIZE_MB: int = 50
    ENABLE_UPLOAD_ENDPOINT: bool = True

    # 音频输出
    AUDIO_OUTPUT_FORMAT: Literal["base64", "url", "both"] = "base64"

    def __init__(self, **data):
        super().__init__(**data)
        for dir_path in [self.TEMP_AUDIO_DIR, self.OUTPUT_AUDIO_DIR, self.LOG_DIR]:
            os.makedirs(dir_path, exist_ok=True)

    @property
    def cors_origins(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

settings = Settings()
