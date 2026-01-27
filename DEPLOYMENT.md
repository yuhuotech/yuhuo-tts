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

## 方案 A: 本地部署

### 第1步: 环境准备

```bash
cd /data/www/yuhuo-tts

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

编辑 `.env` 文件根据需要修改配置。关键配置项：
- API_HOST: API 监听地址 (0.0.0.0 表示所有地址)
- API_PORT: API 端口 (默认 8000)
- DEFAULT_TTS_MODEL: 默认模型
- LOG_LEVEL: 日志级别

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

## 方案 B: Docker 部署

### 第1步: 准备模型

```bash
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

## 访问方式

### 本地访问（开发）
- API: http://localhost:8000
- 文档: http://localhost:8000/docs

### 获取 API URL

服务启动后，所有端点都通过以下 URL 格式访问：
```
http://[HOST]:[PORT]/[endpoint]
```

**完整的公网部署指南详见 CLOUD_DEPLOYMENT.md**
