# 🚀 完整部署指南

## 快速部署（推荐）

### 本地开发环境（macOS）

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 启动 API 服务
python app.py

# 3. 访问
# http://localhost:8000/docs
```

---

## 服务器部署

### 前置条件

**系统要求:**
- Linux (Ubuntu 20.04+ 或 CentOS 8+)
- Python 3.10+
- 16GB RAM 以上
- 20GB 可用磁盘空间（用于模型）
- GPU 推荐 (NVIDIA A10, V100, A100)

**网络要求:**
- 能访问外网（下载模型）
  - modelscope.cn（推荐，中国国内）
  - huggingface.co（备选）

### 部署步骤

#### Step 1: 克隆项目

```bash
# 克隆项目
git clone <项目地址> /opt/tts-api
cd /opt/tts-api

# 或者从 macOS 复制文件
# 将整个项目文件夹通过 scp 复制到服务器
# scp -r /path/to/yuhuo-tts user@server:/opt/tts-api
```

#### Step 2: 运行自动安装脚本

```bash
# 给脚本执行权限
chmod +x scripts/install.sh

# 运行安装脚本（会自动完成所有步骤）
bash scripts/install.sh

# 这个过程会：
# ✅ 创建虚拟环境
# ✅ 安装 Python 依赖
# ✅ 下载 TTS 模型 (8+ GB)
# ✅ 下载 MFA 模型 (100MB)
# ✅ 验证安装
#
# 耗时: 30-60 分钟（取决于网络）
```

#### Step 3: 启动服务

**开发模式:**
```bash
source venv/bin/activate
python app.py
```

**生产模式 (Gunicorn):**
```bash
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

**后台运行 (nohup):**
```bash
source venv/bin/activate
nohup python app.py > logs/app.log 2>&1 &
```

**Docker 部署:**
```bash
docker-compose up -d
```

---

## 手动安装步骤（如果自动脚本失败）

```bash
# 1. 创建虚拟环境
python3.10 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 升级 pip
pip install --upgrade pip setuptools wheel

# 4. 安装依赖
pip install -r requirements.txt

# 5. 创建目录
mkdir -p models temp_audio output_audio logs

# 6. 下载 TTS 模型
pip install modelscope
modelscope download --model FunAudioLLM/CosyVoice2-0.5B \
    --local_dir ./models/CosyVoice2-0.5B
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
    --local_dir ./models/Qwen3-TTS-12Hz-1.7B-Base

# 7. 下载 MFA 模型（可选）
conda install -c conda-forge montreal-forced-aligner -y
mfa model download acoustic mandarin_mfa
mfa model download dictionary mandarin_mfa

# 8. 启动服务
python app.py
```

---

## 常见部署问题

### Q: 模型下载超时怎么办？

A: 使用国内镜像或分段下载：

```bash
# 方式 1: 手动从 ModelScope 网页下载
# https://modelscope.cn/

# 方式 2: 使用 aria2 加速下载
pip install aria2
aria2c -x 16 <模型下载链接>

# 方式 3: 分开下载到本地，再上传到服务器
# 在 macOS 下载完，再 scp 到服务器
scp -r models/* user@server:/opt/tts-api/models/
```

### Q: GPU 显存不足怎么办？

A: 修改 .env 文件：

```bash
# .env
# 使用 float16 量化节省显存
QWEN3_DTYPE=float16

# 或者用 CPU（很慢）
DEVICE=cpu
```

### Q: 安装时缺少依赖怎么办？

A: 安装系统依赖（Ubuntu）：

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    python3.10-dev \
    python3-pip \
    python3-venv \
    libsndfile1 \
    ffmpeg \
    git
```

### Q: MFA 对齐总是失败怎么办？

A: 这是正常的，降级方案会自动启用。如果要完整支持：

```bash
# 安装 conda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 安装完整的 MFA
conda install -c conda-forge montreal-forced-aligner -y

# 下载模型
mfa model download acoustic mandarin_mfa
mfa model download dictionary mandarin_mfa
```

---

## 生产环境配置

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name tts.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 增大超时时间（合成音频可能需要时间）
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### Systemd 服务

```ini
# /etc/systemd/system/tts-api.service
[Unit]
Description=TTS Alignment API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/tts-api
Environment="PATH=/opt/tts-api/venv/bin"
ExecStart=/opt/tts-api/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tts-api
sudo systemctl start tts-api
sudo systemctl status tts-api
```

### 监控和日志

```bash
# 查看实时日志
tail -f logs/app.log

# 监控 GPU 使用
nvidia-smi -l 1  # 每秒刷新一次

# 监控进程
ps aux | grep python | grep app.py
```

---

## 完整的部署清单

- [ ] 系统环境准备（Python 3.10+, 16GB+ RAM）
- [ ] 项目文件复制到服务器
- [ ] 运行 `bash scripts/install.sh` 完整安装
- [ ] 验证所有模型下载成功
- [ ] 测试 API 启动和基本功能
- [ ] 配置 Nginx 反向代理
- [ ] 配置 Systemd 服务自启动
- [ ] 配置日志轮转
- [ ] 设置监控告警（可选）
- [ ] 准备备份方案

---

## 性能优化

### 增加并发

```bash
# .env
MAX_WORKERS=8  # 默认 4，可增加到 8-16（根据 GPU）
```

### 启用音频缓存

```python
# app.py 中配置缓存
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_synthesize(text, model):
    ...
```

### 使用负载均衡

```bash
# 启动多个实例
gunicorn -w 8 -b 0.0.0.0:8000 app:app  # 8 个进程

# 或用 Nginx 负载均衡
upstream tts_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

---

## 疑难排查

### 查看详细错误日志

```bash
# 增加日志级别
DEBUG=True python app.py

# 查看日志文件
tail -100 logs/app.log

# 实时跟踪
journalctl -u tts-api -f
```

### 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# 获取可用模型
curl http://localhost:8000/models

# 测试合成
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "model": "cosyvoice2"}'
```

### GPU 监控

```bash
# 实时监控
watch -n 1 nvidia-smi

# 查看进程占用
nvidia-smi pmon -i 0
```

---

## 文件结构

部署完成后的目录结构：

```
/opt/tts-api/
├── venv/                           # 虚拟环境
├── models/
│   ├── CosyVoice2-0.5B/           # TTS 模型（4.1GB）
│   └── Qwen3-TTS-12Hz-1.7B-Base/  # TTS 模型（4.2GB）
├── temp_audio/                     # 临时音频文件
├── output_audio/                   # 输出音频文件
├── logs/                           # 应用日志
├── app.py                          # 主应用
├── config.py                       # 配置
├── .env                           # 环境变量
├── requirements.txt               # 依赖列表
├── install.sh                     # 安装脚本
└── README.md                      # 说明文档
```

---

## 总结

**使用 install.sh 脚本:**
```bash
bash scripts/install.sh  # 一键完成所有安装
```

**手动安装:**
```bash
source venv/bin/activate
pip install -r requirements.txt
# 然后手动下载模型
```

**启动服务:**
```bash
python app.py              # 开发模式
gunicorn -w 4 -b 0.0.0.0:8000 app:app  # 生产模式
```

**验证:**
```bash
curl http://localhost:8000/docs  # 查看 API 文档
```

现在可以部署到服务器了！🚀
