# 🚀 快速启动指南

## 前置条件检查

```bash
cd /Users/hmw/data/www/yuhuo-tts

# 检查模型是否完整
python verify_installation.py
```

## 步骤 1: 创建虚拟环境（推荐）

### 方式 A: 使用 Python venv（推荐，无需 conda）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 方式 B: 使用 conda（可选，如果有 conda）

```bash
# 创建虚拟环境
conda create -n tts-api python=3.10 -y

# 激活虚拟环境
conda activate tts-api
```

## 步骤 2: 安装依赖

```bash
# 确保在虚拟环境中
which python  # 应该显示 venv 路径

# 使用国内镜像安装（更快）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 或使用官方源
pip install -r requirements.txt
```

**安装可能需要 3-10 分钟**，主要是 PyTorch。

验证安装：
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import fastapi; print('FastAPI: OK')"
```

## 步骤 3: 启动 API 服务

```bash
# 方式 1: 直接运行（开发模式）
python app.py

# 方式 2: 使用 uvicorn（生产模式）
uvicorn app:app --host 0.0.0.0 --port 8000

# 方式 3: 后台运行
nohup python app.py > logs/app.log 2>&1 &
```

预期输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✓ CosyVoice2 模型加载成功
✓ Qwen3-TTS 模型加载成功
```

## 步骤 4: 测试服务

### 方式 1: 访问 API 文档
```
http://localhost:8000/docs
```

### 方式 2: 运行测试脚本
```bash
python test_api.py
```

### 方式 3: 使用 curl 测试

```bash
# 健康检查
curl http://localhost:8000/health

# 获取可用模型
curl http://localhost:8000/models

# 生成语音（CosyVoice2）
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "model": "cosyvoice2",
    "output_format": "url"
  }'

# 生成语音（Qwen3-TTS）
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "model": "qwen3",
    "output_format": "url"
  }'
```

## 步骤 5: 验证功能

所有端点都应该返回成功响应。查看输出的音频文件：
```bash
ls -lah output_audio/
```

## 常见问题

### Q: 启动时 GPU 内存不足？
A: 模型较大，需要 6-8GB VRAM。如果不足，可以改为 CPU（但会很慢）：
```bash
# 编辑 .env 文件
DEVICE=cpu
```

### Q: 模型加载失败？
A: 检查模型路径：
```bash
# 确认模型目录存在
ls -la models/CosyVoice2-0.5B/
ls -la models/Qwen3-TTS-12Hz-1.7B-Base/

# 检查 .env 配置
grep MODEL .env
```

### Q: 依赖安装失败？
A: 尝试用官方源：
```bash
pip install -r requirements.txt --no-cache-dir
```

### Q: 端口 8000 被占用？
A: 修改端口：
```bash
# 在 .env 中改
API_PORT=8001

# 或直接指定
uvicorn app:app --port 8001
```

## 清理虚拟环境

```bash
# 离开虚拟环境
deactivate

# 删除虚拟环境（如需要）
rm -rf venv/
```

## 停止服务

```bash
# 如果是直接运行（Ctrl+C）
# 如果是后台运行
pkill -f "python app.py"
pkill -f "uvicorn"
```

---

**现在就启动吧！** 🚀
