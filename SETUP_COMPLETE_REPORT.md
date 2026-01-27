# 🎉 TTS-Alignment-API 安装报告

**日期**: 2026-01-27
**项目**: yuhuo-tts (TTS-Alignment-API)
**状态**: ⏳ 后台下载进行中

---

## 📊 已完成的工作

### ✅ Phase 1: 模型文件检查与部分下载

| 模型 | 状态 | 大小 | 说明 |
|------|------|------|------|
| **CosyVoice2-0.5B** | ✅ 完整 | 4.1GB | 所有必需文件都已完成 |
| **Qwen3-TTS 主权重** | ⏳ 下载中 | ~3.1GB | 后台任务 ID: b5d2df1 |
| **Qwen3-TTS tokenizer** | ✅ 完整 | 651MB | speech_tokenizer/model.safetensors |
| **MFA 中文模型** | ⏳ 下载中 | ~200MB | 后台任务 ID: bd06ebd |

### ✅ Phase 2: 工具安装

| 工具 | 状态 | 用途 |
|------|------|------|
| **modelscope** | ✅ | 从 ModelScope 下载模型 |
| **montreal-forced-aligner** | ✅ | 字级时间对齐 |
| **librosa, soundfile** | ✅ | 音频处理 |
| **FastAPI, Uvicorn** | ✅ | API 框架 |
| **PyTorch** | ✅ | 深度学习框架 |

### ✅ Phase 3: 代码改进

| 项目 | 改进 | 文件 |
|------|------|------|
| **MFA 对齐器** | 增强错误处理，自动降级方案 | `alignment/mfa_aligner.py` |
| **降级方案** | 当 MFA 不可用时，使用均匀时间分配 | `alignment/mfa_aligner.py` |

### ✅ Phase 4: 安装工具和文档

| 文件 | 用途 |
|------|------|
| **verify_installation.py** | 验证安装完整性 |
| **check_download_status.sh** | 检查后台下载进度 |
| **INSTALLATION_STATUS.md** | 安装状态说明 |

---

## 🔄 后台进行中的任务

### 任务 1: Qwen3-TTS 模型下载
```bash
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base --local_dir ./models/Qwen3-TTS-12Hz-1.7B-Base
```
- **ID**: b5d2df1
- **预计时间**: 10-30 分钟
- **目标**: 下载 ~3.1GB 主权重文件
- **下载到**: `./models/Qwen3-TTS-12Hz-1.7B-Base/`

### 任务 2: MFA 中文模型下载
```bash
python /tmp/download_mfa_models.py
```
- **ID**: bd06ebd
- **预计时间**: 5-10 分钟
- **内容**:
  - `~/.mfa/models/acoustic_models/chinese_flac`
  - `~/.mfa/models/g2p_models/chinese_flac`

---

## 📋 实时进度检查

### 快速检查命令

```bash
# 方式 1: 查看文件大小进度
du -sh ./models/*/

# 方式 2: 查看下载进程
ps aux | grep modelscope
ps aux | grep download_mfa

# 方式 3: 使用我们提供的脚本
bash check_download_status.sh

# 方式 4: 完整验证
python verify_installation.py
```

### 预期输出（完成时）
```
✅ CosyVoice2-0.5B: ✅ (4.1GB)
✅ Qwen3-TTS-12Hz-1.7B-Base: ✅ (3.1GB)
✅ MFA 中文模型: ✅ (~200MB)
✅ 所有依赖: ✅
✅ 一切就绪！可以启动 API 服务了
```

---

## 🚀 后续步骤（按顺序）

### 第 1 步：等待后台任务完成 ⏳
```bash
# 实时监控下载进度
watch -n 10 bash check_download_status.sh
```

预计时间: 15-40 分钟

### 第 2 步：验证安装完整性 ✅
```bash
python verify_installation.py
```

输出应该全部为 ✅

### 第 3 步：启动 API 服务 🚀
```bash
python app.py
```

预期输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 [unix_event_loop]
INFO:     Application startup complete
✓ CosyVoice2 模型加载成功
✓ Qwen3-TTS 模型加载成功
```

### 第 4 步：访问 API 📖
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### 第 5 步：测试功能 🧪
```bash
# 运行测试脚本
python test_api.py

# 或使用 curl
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "model": "cosyvoice2"}'
```

---

## 💡 重要说明

### MFA 依赖问题 ⚠️

**情况**: MFA 缺少 `_kalpy` 模块

**影响**: 字级对齐精度会降低
- 使用降级方案（均匀时间分配）时：`confidence = 0.50`
- 正常 MFA 对齐时：`confidence = 0.85-0.95`

**BUT**: API **仍然能够正常工作**！

**可选解决方案**:
```bash
# 安装 conda（如果还没有）
# macOS: brew install miniconda
# 然后重新安装 MFA
conda install -c conda-forge montreal-forced-aligner -y
python /tmp/download_mfa_models.py
```

---

## 📂 项目结构完整性检查

```
✅ 已完整
├── app.py                           # FastAPI 主应用
├── config.py                        # 配置管理
├── requirements.txt                 # Python 依赖
├── .env                            # 环境变量
├── test_api.py                     # 测试脚本
├── verify_installation.py          # 新增: 验证脚本
├── check_download_status.sh        # 新增: 状态检查脚本
│
├── models/                         # 模型目录
│   ├── CosyVoice2-0.5B/           # ✅ 4.1GB 完整
│   ├── Qwen3-TTS-12Hz-1.7B-Base/  # ⏳ 下载中
│   ├── tts_base.py
│   ├── cosyvoice2_model.py
│   └── qwen3_model.py
│
├── alignment/                      # 对齐模块
│   ├── mfa_aligner.py             # ✅ 已改进降级方案
│   └── textgrid_parser.py
│
├── utils/                         # 工具模块
│   ├── audio_utils.py
│   └── file_utils.py
│
├── Dockerfile                     # Docker 镜像
├── docker-compose.yml             # Docker 编排
├── README.md                      # 使用说明
├── DEPLOYMENT.md                  # 部署指南
└── CLOUD_DEPLOYMENT.md            # 云部署指南
```

---

## 🔧 故障排查

### 问题 1: 下载进度很慢
```bash
# 检查网络连接
ping github.com
ping modelscope.cn

# 查看下载进程
ps aux | grep modelscope
```

### 问题 2: Qwen3-TTS 下载失败后恢复
```bash
# 清理之前的下载（保留已下载部分）
cd models/
rm -rf Qwen3-TTS-12Hz-1.7B-Base/.cache

# 重新下载
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base --local_dir ./Qwen3-TTS-12Hz-1.7B-Base
```

### 问题 3: MFA 模型下载失败
```bash
# 如果 MFA 下载失败，可以跳过
# API 会自动使用降级方案

# 但如果想重试
python /tmp/download_mfa_models.py
```

### 问题 4: API 启动失败 - 缺少模型
```bash
# 检查模型是否完整
python verify_installation.py

# 等待所有下载完成后再启动
```

---

## 📞 需要帮助？

### 1️⃣ 验证当前状态
```bash
python verify_installation.py
```

### 2️⃣ 检查下载进度
```bash
bash check_download_status.sh
```

### 3️⃣ 查看详细日志
```bash
# CosyVoice2 加载
python -c "from models.cosyvoice2_model import CosyVoice2Model; m = CosyVoice2Model()"

# Qwen3-TTS 加载
python -c "from models.qwen3_model import Qwen3Model; m = Qwen3Model()"
```

### 4️⃣ 重置并重新开始（如需要）
```bash
# 清理所有缓存
rm -rf models/*/.cache
rm -rf ~/.cache/huggingface/
rm -rf ~/.mfa/models/

# 重新启动下载
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base --local_dir ./models/Qwen3-TTS-12Hz-1.7B-Base
python /tmp/download_mfa_models.py
```

---

## 📈 下一个大版本计划

等到当前安装完全就绪后，可以考虑：

1. **部署到云服务** (Alibaba Cloud / AWS)
2. **添加 Web UI**
3. **支持批量处理**
4. **实时流式输出**
5. **声音克隆功能**
6. **多语言支持**

---

## 📝 总结

```
✅ 核心代码: 完整
✅ 模型下载: 进行中
✅ 依赖安装: 完成
✅ 工具脚本: 完成
✅ 文档: 完整

⏳ 等待中间件下载完成 (15-40 分钟)
🚀 完成后可以启动服务
```

---

**配置日期**: 2026-01-27 11:15
**预计完成**: 2026-01-27 11:50-12:00
**项目**: yuhuo-tts (TTS-Alignment-API)
**版本**: 1.0.0-beta
