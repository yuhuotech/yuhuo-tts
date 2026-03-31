# YuHuo TTS

一个基于 FastAPI 的 TTS API 服务，提供：

- CosyVoice2 与 Qwen3-TTS 双模型接入
- 音频合成结果输出为 `base64` 或文件 URL
- MFA 对齐，失败时自动降级为均匀时间分配
- 音频上传接口，可返回 `prompt_audio` 路径供克隆模式使用

## 当前状态

项目已经具备基本功能闭环，但仍依赖外部模型、第三方源码仓库和 GPU 环境。

- 适合公开源码
- 不适合把模型权重、真实环境变量或部署产物一起公开
- 第三方模型和源码需按各自许可证单独安装和使用

## 开源前已处理

- 仓库默认忽略 `.env`、`.env.cloud`、`models/`、`third_party/`
- 提供 `.env.example` 和 `.env.cloud.example`
- Docker 与默认配置统一使用 `models/` 目录
- 服务启动时允许部分模型加载失败，只要至少有一个模型可用就能启动

## 目录约定

```text
.
├── app.py
├── config.py
├── scripts/
│   ├── install.sh
│   ├── run.sh
│   ├── test_api.py
│   └── verify_installation.py
├── models/
│   ├── cosyvoice2_model.py
│   └── qwen3_model.py
├── alignment/
├── utils/
├── .env.example
└── .env.cloud.example
```

## 环境要求

- Python 3.10+
- NVIDIA GPU + CUDA
- 16 GB+ RAM
- 20 GB+ 磁盘空间用于模型

## 快速开始

### 1. 准备配置

```bash
cp .env.example .env
```

### 2. 安装依赖

推荐直接使用安装脚本：

```bash
bash scripts/install.sh
```

它会执行这些步骤：

- 创建 `venv`
- 安装 Python 依赖
- 安装 Qwen3-TTS Python 包
- 克隆 `third_party/CosyVoice`
- 下载 CosyVoice2 / Qwen3-TTS 模型到 `models/`
- 检查 MFA

### 3. 启动服务

```bash
bash scripts/run.sh
```

服务默认监听 `http://localhost:8000`。

## 手动安装

如果不想使用脚本，至少需要完成下面几步：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install git+https://github.com/QwenLM/Qwen3-TTS.git
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git third_party/CosyVoice
```

然后下载模型：

```bash
modelscope download --model iic/CosyVoice2-0.5B \
  --local_dir ./models/CosyVoice2-0.5B

modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --local_dir ./models/Qwen3-TTS-12Hz-1.7B-Base
```

如需真实 MFA 对齐，还需要安装 Montreal Forced Aligner 并下载对应模型：

```bash
mfa model download acoustic mandarin_mfa
mfa model download dictionary mandarin_mfa
```

## API

### `GET /health`

返回服务状态、已加载模型和 MFA 开关状态。模型加载失败时会显示错误信息。

### `GET /models`

返回每个模型的状态、采样率、可用音色和错误信息。

### `POST /synthesize`

请求示例：

```json
{
  "text": "你好，这是一个测试。",
  "model": "cosyvoice2",
  "mode": "sft",
  "output_format": "base64"
}
```

### `POST /upload_audio`

上传音频后，响应里的 `prompt_audio` 可直接作为克隆模式的 `prompt_audio` 参数。

## Docker

先准备云环境配置：

```bash
cp .env.cloud.example .env.cloud
docker compose up -d --build
```

默认挂载目录：

- `./models -> /app/models`
- `./output_audio -> /app/output_audio`
- `./logs -> /app/logs`
- `./temp_audio -> /app/temp_audio`

说明：Docker 镜像构建时会安装第三方 TTS 依赖，但模型文件仍建议放在宿主机挂载目录中。

## 不应公开的内容

这些内容不应提交到公开仓库：

- `.env`
- `.env.cloud`
- `models/`
- `third_party/`
- `logs/` 下的真实日志
- `temp_audio/`、`output_audio/` 下的实际音频文件

## 许可证

本仓库代码采用 MIT 许可证；第三方依赖、模型源码与模型权重仍需分别遵守各自许可证与使用条款。
