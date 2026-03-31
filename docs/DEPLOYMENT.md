# TTS-Alignment-API 部署指南

## 前置条件

### 系统需求

- Ubuntu 20.04+ / CentOS 8+ / Rocky / AlmaLinux / macOS 12+
- 建议 16GB+ 内存
- 建议 20GB+ 可用磁盘
- GPU 可选，CPU 也能跑，但更慢

### Linux 基础依赖

Ubuntu / Debian:

```bash
sudo apt update
sudo apt install -y git curl build-essential ffmpeg
```

CentOS / RHEL / Rocky / AlmaLinux:

```bash
sudo yum install -y git curl gcc gcc-c++ make ffmpeg
```

较新的系统也可以用：

```bash
sudo dnf install -y git curl gcc gcc-c++ make ffmpeg
```

## 方案 A: 本地部署

### 推荐方式

```bash
git clone https://github.com/yuhuotech/yuhuo-tts.git
cd yuhuo-tts
bash scripts/install.sh
bash scripts/run.sh
```

安装脚本会自动：

- 准备 `.env`
- 安装或检测 `uv`
- 同步 Python 依赖
- 克隆 CosyVoice
- 下载 `DEFAULT_TTS_MODEL` 对应模型
- 在 `MFA_ENABLE=True` 时安装和验收 MFA

### 手动方式

```bash
cp .env.example .env
uv sync
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git third_party/CosyVoice
uv pip install --no-build-isolation HyperPyYAML==1.2.3 hydra-core==1.3.2 omegaconf==2.3.0 inflect==7.3.1 wetext==0.0.4 conformer==0.3.2 diffusers==0.29.0 gdown==5.1.0 x-transformers==2.11.24 lightning==2.2.4 openai-whisper==20231117 protobuf==4.25.0 pyarrow==18.1.0 rich==13.7.1 wget==3.2
```

如需真实 MFA 对齐：

```bash
bash scripts/install_mfa.sh
```

### 启动

```bash
bash scripts/run.sh
```

### 测试

```bash
curl http://127.0.0.1:8000/health
uv run python scripts/test_api.py
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
