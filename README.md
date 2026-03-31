# YuHuo TTS

一个面向服务化部署的 TTS API 项目，基于 FastAPI 封装 CosyVoice2、Qwen3-TTS 和 MFA 对齐能力，提供统一的文本转语音、音频输出和时间戳接口。

## Overview

YuHuo TTS 解决的是“把本地模型能力整理成可调用 API”的问题，重点不是训练模型，而是把推理、文件输出、上传参考音频、时间戳对齐和部署入口串成一个可落地的服务。

适合的场景：

- 提供统一的 TTS HTTP API，可接入网站、应用、自动化流程或其他服务
- 在多模型之间切换，比较音色、速度和适用场景
- 为字幕、高亮朗读、逐字播放等功能生成时间戳
- 把本地推理环境整理为可复用的部署仓库

## Features

- 双模型接入：统一封装 `CosyVoice2` 和 `Qwen3-TTS`
- 统一合成接口：通过同一个 `/synthesize` API 调不同模型
- 多种音频输出：支持 `base64`、文件 URL、或两者同时返回
- 时间戳对齐：优先使用 MFA，对齐不可用时自动降级
- 参考音频上传：支持上传音频并将返回值直接作为 `prompt_audio`
- 启动容错：允许部分模型加载失败，只要至少有一个模型可用，服务仍可启动
- Docker 入口：提供容器化部署配置
- 开源清理完成：环境变量、模型、第三方源码和产物目录已从仓库规范隔离

## Architecture

核心流程如下：

1. API 接收文本、模型选择和输出选项
2. 对应模型执行 TTS 推理
3. 音频做基础规范化处理
4. MFA 执行文本与音频对齐
5. 返回音频、时长、采样率、时间戳和文件信息

主要目录：

```text
.
├── app.py                      # FastAPI 应用入口
├── config.py                   # 配置加载
├── alignment/                  # MFA 对齐与 TextGrid 处理
├── models/                     # 模型适配层
├── utils/                      # 音频与文件工具
├── scripts/                    # 安装、启动、测试、检查脚本
├── docs/                       # 部署与补充文档
├── .env.example
├── .env.cloud.example
└── docker-compose.yml
```

## Model Support

### CosyVoice2

- 默认采样率 `22050`
- 支持 `sft`、`zero_shot`、`cross_lingual`、`instruct`
- 适合更完整的音色和克隆类场景

### Qwen3-TTS

- 默认采样率 `24000`
- 通过独立的 pipeline 接入
- 更适合统一的文本转语音接口和多模型对比

## Alignment Strategy

项目采用“优先精确、失败降级”的策略：

- 如果 MFA 可用，则执行真实对齐
- 如果 MFA 缺失、超时或失败，则退化为均匀时间分配
- 因此 API 层不会因为对齐组件异常而整体不可用

这保证了服务可用性，但也意味着：

- 有 MFA 时，时间戳更有参考价值
- 无 MFA 时，时间戳只适合粗粒度播放控制，不适合高精度字幕

## API Summary

### `GET /health`

返回服务健康状态、模型加载情况和 MFA 开关状态。

### `GET /models`

返回每个模型的：

- 加载状态
- 采样率
- 可用音色
- 错误信息

### `POST /synthesize`

用于文本转语音和时间戳生成。

请求示例：

```json
{
  "text": "你好，这是一个测试。",
  "model": "cosyvoice2",
  "mode": "sft",
  "output_format": "base64"
}
```

返回数据包含：

- `audio` 或 `audio_url`
- `alignments`
- `duration`
- `sample_rate`
- `model_used`

### `POST /upload_audio`

上传参考音频后，会返回：

- `file_id`
- `filename`
- `size`
- `prompt_audio`

其中 `prompt_audio` 可以直接回传给 `/synthesize` 的 `prompt_audio` 参数。

## Quick Start

### 1. Prepare config

```bash
cp .env.example .env
```

### 2. Install dependencies

推荐直接使用脚本：

```bash
bash scripts/install.sh
```

这个脚本会：

- 创建 `venv`
- 安装 Python 依赖
- 安装 `Qwen3-TTS` Python 包
- 克隆 `third_party/CosyVoice`
- 下载 CosyVoice2 和 Qwen3-TTS 模型到 `models/`
- 检查并初始化 MFA 相关依赖

### 3. Start the API

```bash
bash scripts/run.sh
```

默认地址：

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

### 4. Verify installation

```bash
python scripts/verify_installation.py
python scripts/test_api.py
```

## Manual Setup

如果你不想使用安装脚本，至少需要完成这些步骤：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install git+https://github.com/QwenLM/Qwen3-TTS.git
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git third_party/CosyVoice
```

下载模型：

```bash
modelscope download --model iic/CosyVoice2-0.5B \
  --local_dir ./models/CosyVoice2-0.5B

modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --local_dir ./models/Qwen3-TTS-12Hz-1.7B-Base
```

如需真实 MFA 对齐：

```bash
mfa model download acoustic mandarin_mfa
mfa model download dictionary mandarin_mfa
```

## Configuration

示例配置见：

- [`.env.example`](/Users/hmw/data/www/yuhuo-tts/.env.example)
- [`.env.cloud.example`](/Users/hmw/data/www/yuhuo-tts/.env.cloud.example)

常用配置项：

- `DEFAULT_TTS_MODEL`
- `COSYVOICE_MODEL_DIR`
- `QWEN3_MODEL_DIR`
- `MFA_ENABLE`
- `AUDIO_OUTPUT_FORMAT`
- `MAX_FILE_SIZE_MB`
- `OUTPUT_AUDIO_DIR`

## Docker

先准备云环境配置：

```bash
cp .env.cloud.example .env.cloud
docker compose up -d --build
```

默认挂载：

- `./models -> /app/models`
- `./output_audio -> /app/output_audio`
- `./logs -> /app/logs`
- `./temp_audio -> /app/temp_audio`

说明：

- 镜像会安装第三方 Python 依赖和 CosyVoice 源码依赖
- 模型权重仍建议放在宿主机挂载目录中
- 如果你要做公网服务，建议额外在反向代理层补鉴权和限流

## Scripts

仓库把辅助脚本集中放在 `scripts/`：

- [scripts/install.sh](/Users/hmw/data/www/yuhuo-tts/scripts/install.sh): 一键安装依赖与模型
- [scripts/run.sh](/Users/hmw/data/www/yuhuo-tts/scripts/run.sh): 启动服务
- [scripts/verify_installation.py](/Users/hmw/data/www/yuhuo-tts/scripts/verify_installation.py): 检查依赖和目录
- [scripts/test_api.py](/Users/hmw/data/www/yuhuo-tts/scripts/test_api.py): 调用 API 做集成测试
- [scripts/test_cosyvoice.py](/Users/hmw/data/www/yuhuo-tts/scripts/test_cosyvoice.py): 检查 CosyVoice 环境
- [scripts/test_mfa_chinese.py](/Users/hmw/data/www/yuhuo-tts/scripts/test_mfa_chinese.py): 检查 MFA 中文对齐

## Docs

补充文档放在 `docs/`：

- [docs/QUICK_START.md](/Users/hmw/data/www/yuhuo-tts/docs/QUICK_START.md)
- [docs/DEPLOYMENT.md](/Users/hmw/data/www/yuhuo-tts/docs/DEPLOYMENT.md)
- [docs/DEPLOYMENT_GUIDE.md](/Users/hmw/data/www/yuhuo-tts/docs/DEPLOYMENT_GUIDE.md)
- [docs/CLOUD_DEPLOYMENT.md](/Users/hmw/data/www/yuhuo-tts/docs/CLOUD_DEPLOYMENT.md)
- [docs/MFA_SETUP_GUIDE.md](/Users/hmw/data/www/yuhuo-tts/docs/MFA_SETUP_GUIDE.md)

## License

本仓库代码采用 [MIT License](/Users/hmw/data/www/yuhuo-tts/LICENSE)。

注意：

- CosyVoice2、Qwen3-TTS、MFA 及其模型权重有各自独立的许可证与使用条款
- 在商用或公网服务场景中，请分别核对第三方组件与模型的合规要求
