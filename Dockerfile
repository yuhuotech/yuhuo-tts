FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

LABEL description="TTS-Alignment-API: Multi-model TTS with MFA Forced Alignment"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    git-lfs \
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

# 安装第三方 TTS 依赖
RUN git lfs install \
    && git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git /opt/CosyVoice \
    && pip install -r /opt/CosyVoice/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
    && pip install git+https://github.com/QwenLM/Qwen3-TTS.git -i https://mirrors.aliyun.com/pypi/simple/

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs temp_audio output_audio models

# CosyVoice 运行时需要源码和 Matcha-TTS 子模块
ENV PYTHONPATH="/opt/CosyVoice:/opt/CosyVoice/third_party/Matcha-TTS:${PYTHONPATH}"

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动应用
CMD ["python", "app.py"]
