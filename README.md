# YuHuo TTS - 语音合成 + 字级对齐服务

> 一个生产级的 TTS 语音合成 + MFA 字级对齐 API 服务，支持 CosyVoice2 和 Qwen3-TTS 双模型。

## 🚀 快速开始

### 环境要求
- Python 3.10+
- NVIDIA GPU with CUDA 11.8+
- 16GB+ RAM
- 20GB+ 存储空间（用于模型）

### 1. 克隆项目
```bash
cd /data/www/yuhuo-tts
```

### 2. 安装依赖
```bash
conda create -n tts-api python=3.10
conda activate tts-api
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
conda install -c conda-forge montreal-forced-aligner
```

### 3. 下载模型
```bash
# CosyVoice2
modelscope download --model FunAudioLLM/CosyVoice2-0.5B \
  --local_dir pretrained_models/CosyVoice2-0.5B

# Qwen3-TTS
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --local_dir pretrained_models/Qwen3-TTS-12Hz-1.7B-Base

# MFA模型
mfa model download acoustic chinese_flac
mfa model download dictionary chinese_flac
```

### 4. 启动服务
```bash
python app.py
```

服务将在 `http://localhost:8000` 运行

### 5. 测试 API
```bash
python test_api.py
```

## 📚 API 文档

### 合成语音

**端点**: `POST /synthesize`

**请求示例**:
```json
{
  "text": "你好世界",
  "model": "cosyvoice2",
  "mode": "sft",
  "output_format": "base64"
}
```

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "audio": "UklGRi4AAAA...",
    "alignments": [
      {"char": "你", "start": 0.0, "end": 0.45, "confidence": 0.92},
      {"char": "好", "start": 0.45, "end": 0.9, "confidence": 0.91}
    ],
    "duration": 2.45,
    "sample_rate": 22050
  }
}
```

### 获取可用模型

**端点**: `GET /models`

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "cosyvoice2": {"sample_rate": 22050, "speakers": ["default"]},
    "qwen3": {"sample_rate": 24000, "speakers": ["default"]}
  }
}
```

## 📊 功能特性

- ✅ 双模型支持 (CosyVoice2 + Qwen3-TTS)
- ✅ 字级时间戳对齐 (MFA)
- ✅ 多格式输出 (base64/URL)
- ✅ 文件上传功能
- ✅ 生产级日志和监控
- ✅ Docker 容器化
- ✅ 完整 API 文档

## 🔧 配置

编辑 `.env` 文件进行配置：

```bash
# TTS模型
DEFAULT_TTS_MODEL=cosyvoice2

# API端口
API_PORT=8000

# MFA对齐
MFA_ENABLE=True

# 日志级别
LOG_LEVEL=INFO
```

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t tts-alignment-api:latest .

# 运行容器
docker-compose up -d

# 查看日志
docker logs -f tts-alignment-api
```

## 📖 完整文档

详见 `docs/` 目录：
- `TTS_Alignment_完整方案.md` - 技术架构
- `快速开始指南.md` - 详细部署
- `工具函数和辅助代码.md` - API 参考
- `项目总结与行动计划.md` - 优化指南

## 🤝 支持

遇到问题？查看 `docs/文档导航和快速参考.md` 的故障排查部分。

## 📄 许可证

按 CosyVoice2 和 Qwen3-TTS 的许可证使用。

---

**最后更新**: 2026-01-27
