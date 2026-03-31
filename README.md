# YuHuo TTS

一个面向服务化部署的 TTS API 项目，基于 FastAPI 封装 CosyVoice2、Qwen3-TTS 和 MFA 对齐能力，提供统一的文本转语音、音频输出和时间戳接口。

## Quick Start

新用户现在只需要这两步：

```bash
git clone git@github.com:yuhuotech/yuhuo-tts.git
cd yuhuo-tts
bash scripts/install.sh
bash scripts/run.sh
```

如果你在 Linux 上，支持的主路径是：

- Ubuntu 20.04+
- CentOS 8+ / Rocky Linux / AlmaLinux
- macOS 12+

默认行为：

- 自动生成 `.env`
- 按 `DEFAULT_TTS_MODEL` 只下载一个模型
- 自动安装 CosyVoice 运行依赖
- 如果 `MFA_ENABLE=True`，自动安装并验收 MFA

默认地址：

- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

推荐先保持默认配置，资源压力最小：

```env
DEFAULT_TTS_MODEL=cosyvoice2
MFA_ENABLE=True
MFA_FALLBACK_ALIGNMENT=none
```

## Linux Support

项目现在不只按 macOS 来设计，安装脚本已经考虑了 Linux。

在 Ubuntu 上，建议先准备：

```bash
sudo apt update
sudo apt install -y git curl build-essential ffmpeg
```

在 CentOS / RHEL / Rocky / AlmaLinux 上，建议先准备：

```bash
sudo yum install -y git curl gcc gcc-c++ make ffmpeg
```

如果系统较新，也可以使用：

```bash
sudo dnf install -y git curl gcc gcc-c++ make ffmpeg
```

之后统一执行：

```bash
bash scripts/install.sh
bash scripts/run.sh
```

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
- 时间戳对齐：优先使用 MFA，可配置为失败时不输出或降级均分
- 参考音频上传：支持上传音频并通过 `uploaded_audio_id` 在后续合成请求中复用
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

项目采用“优先精确、可配置回退”的策略：

- 如果 MFA 可用，则执行真实对齐
- 如果 MFA 缺失、超时或失败，则按 `MFA_FALLBACK_ALIGNMENT` 决定行为
- `none`: 不输出时间戳，`alignments` 返回空数组
- `uniform`: 退化为均匀时间分配
- 因此 API 层不会因为对齐组件异常而整体不可用

这保证了服务可用性，但也意味着：

- 有 MFA 时，时间戳更有参考价值
- 无 MFA 且 `MFA_FALLBACK_ALIGNMENT=uniform` 时，时间戳只适合粗粒度播放控制，不适合高精度字幕

当前 `/health` 会返回 `mfa_status`，其中包含：

- `available`
- `command_available`
- `command_path`
- `command_error`
- `acoustic_model_path`
- `dictionary_path`
- `fallback_alignment`
- `reason`

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
- `uploaded_audio_id`

推荐在 `/synthesize` 中使用 `uploaded_audio_id` 引用已上传文件。
兼容场景下也可以直接传本地 `prompt_audio` 路径，但那更适合同机部署或可信环境。

## Install Flow

项目建议使用 Python `3.12`，仓库已通过 [`.python-version`](/Users/hmw/data/www/yuhuo-tts/.python-version) 固定给 `uv`。

[`scripts/install.sh`](/Users/hmw/data/www/yuhuo-tts/scripts/install.sh) 现在是唯一推荐安装入口。它会自动完成：

- 没有 `.env` 时，从 [`.env.example`](/Users/hmw/data/www/yuhuo-tts/.env.example) 生成
- 缺少 `uv` 时尝试自动安装
- `uv sync`
- 克隆 `third_party/CosyVoice`
- 安装 CosyVoice 运行依赖
- 按 `DEFAULT_TTS_MODEL` 下载一个模型
- 在 `MFA_ENABLE=True` 时执行 [`scripts/install_mfa.sh`](/Users/hmw/data/www/yuhuo-tts/scripts/install_mfa.sh)
- 运行 [`scripts/verify_installation.py`](/Users/hmw/data/www/yuhuo-tts/scripts/verify_installation.py)

切换模型时，改完 `.env` 再重跑一次安装脚本即可：

```env
DEFAULT_TTS_MODEL=qwen3
```

## Manual Setup

如果你不想使用一键脚本，至少需要完成这些步骤：

```bash
cp .env.example .env
uv sync
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git third_party/CosyVoice
uv pip install --no-build-isolation HyperPyYAML==1.2.3 hydra-core==1.3.2 omegaconf==2.3.0 inflect==7.3.1 wetext==0.0.4 conformer==0.3.2 diffusers==0.29.0 gdown==5.1.0 x-transformers==2.11.24 lightning==2.2.4 openai-whisper==20231117 protobuf==4.25.0 pyarrow==18.1.0 rich==13.7.1 wget==3.2
```

按 `.env` 里的默认模型下载权重：

```bash
uv run modelscope download --model iic/CosyVoice2-0.5B \
  --local_dir ./models/CosyVoice2-0.5B
```

如需真实 MFA 对齐：

```bash
bash scripts/install_mfa.sh
```

如果 `uv` 环境里的 MFA CLI 不可用，`scripts/install_mfa.sh` 会自动回退到系统 `PATH` 中的 `mfa`。

## Configuration

示例配置见：

- [`.env.example`](/Users/hmw/data/www/yuhuo-tts/.env.example)
- [`.env.cloud.example`](/Users/hmw/data/www/yuhuo-tts/.env.cloud.example)

常用配置项：

- `DEFAULT_TTS_MODEL`
- `COSYVOICE_MODEL_DIR`
- `QWEN3_MODEL_DIR`
- `MFA_ENABLE`
- `MFA_FALLBACK_ALIGNMENT`
- `MFA_ACOUSTIC_MODEL`
- `MFA_DICTIONARY`
- `CORS_ORIGINS`
- `CORS_ALLOW_CREDENTIALS`
- `AUDIO_OUTPUT_FORMAT`
- `MAX_FILE_SIZE_MB`
- `OUTPUT_AUDIO_DIR`

说明：

- `DEFAULT_TTS_MODEL` 控制服务启动时实际加载哪个模型
- `scripts/install.sh` 只会下载 `DEFAULT_TTS_MODEL` 对应的模型
- 如果你只想降低本机内存和 CPU 压力，建议设置为 `DEFAULT_TTS_MODEL=cosyvoice2`

## Dependency Management

- 项目依赖由 [`pyproject.toml`](/Users/hmw/data/www/yuhuo-tts/pyproject.toml) 管理
- 推荐使用 `uv sync` 安装和更新依赖
- 推荐使用 `uv run ...` 执行脚本和启动服务
- MFA CLI 优先从当前 `PATH` 或项目 `.venv/bin/mfa` 解析

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
- [scripts/install_mfa.sh](/Users/hmw/data/www/yuhuo-tts/scripts/install_mfa.sh): 单独安装和验收 MFA
- [scripts/run.sh](/Users/hmw/data/www/yuhuo-tts/scripts/run.sh): 使用 `uv` 启动服务
- [scripts/verify_installation.py](/Users/hmw/data/www/yuhuo-tts/scripts/verify_installation.py): 检查依赖和目录
- [scripts/test_api.py](/Users/hmw/data/www/yuhuo-tts/scripts/test_api.py): 调用 API 做集成测试
- [scripts/test_cosyvoice.py](/Users/hmw/data/www/yuhuo-tts/scripts/test_cosyvoice.py): 检查 CosyVoice 环境
- [scripts/test_mfa_chinese.py](/Users/hmw/data/www/yuhuo-tts/scripts/test_mfa_chinese.py): 检查 MFA 中文对齐
- [scripts/check_mfa_ready.py](/Users/hmw/data/www/yuhuo-tts/scripts/check_mfa_ready.py): 检查 MFA 命令、模型、词典和回退策略

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
