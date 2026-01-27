# 安装进度追踪

## 后台下载任务

### 1️⃣ Qwen3-TTS 模型下载
- **任务 ID**: b5d2df1
- **状态**: ⏳ 进行中
- **预计时间**: 10-30 分钟
- **大小**: ~3.1GB
- **命令**:
  ```bash
  modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base --local_dir ./models/Qwen3-TTS-12Hz-1.7B-Base
  ```

### 2️⃣ MFA 模型下载
- **任务 ID**: bd06ebd
- **状态**: ⏳ 进行中
- **预计时间**: 5-10 分钟
- **内容**:
  - 中文声学模型 (acoustic)
  - 中文字典 (dictionary)
- **命令**:
  ```bash
  python /tmp/download_mfa_models.py
  ```

## 已完成 ✅

| 项目 | 状态 | 说明 |
|------|------|------|
| CosyVoice2-0.5B | ✅ | 4.1GB, 所有文件完整 |
| Qwen3-TTS speech_tokenizer | ✅ | 651MB, 已下载 |
| Python 依赖 | ✅ | 核心库已安装 |
| modelscope 工具 | ✅ | 用于模型下载 |
| Montreal Forced Aligner | ✅ | 已通过 pip 安装 |

## 进行中 ⏳

| 项目 | 进度 | ETA |
|------|------|------|
| Qwen3-TTS 主权重文件 | 下载中... | 10-30 分钟 |
| MFA 中文模型 | 下载中... | 5-10 分钟 |

## 需要处理 ⚠️

### MFA 依赖问题
MFA 缺少 `_kalpy` 模块（通常需要 conda 安装）。但项目已实现了**降级方案**：
- 如果 MFA 不可用，自动使用**均匀时间分配**
- API 仍然能够正常工作
- 字幕生成精度会略低（confidence: 0.50 vs 0.85-0.95）

**解决方案**（可选）:
```bash
# 如果想完整支持 MFA，安装 conda 后运行：
conda install -c conda-forge montreal-forced-aligner -y
mfa model download acoustic chinese_flac
mfa model download dictionary chinese_flac
```

## 验证安装完整性

等待后台任务完成后，运行：

```bash
python verify_installation.py
```

输出应该显示：
```
✅ CosyVoice2: ✅
✅ Qwen3-TTS: ✅
✅ 所有依赖: ✅
✅ 所有目录: ✅
✅ 一切就绪！可以启动 API 服务了
```

## 启动 API 服务

### 方式 1: 直接运行
```bash
python app.py
```

预期输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✓ CosyVoice2 模型加载成功
✓ Qwen3-TTS 模型加载成功
```

### 方式 2: Docker 运行（需要模型文件完整）
```bash
docker-compose up -d
```

## 快速测试

启动服务后，访问：
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **测试脚本**: `python test_api.py`

## 常见问题

### Q: 如何检查后台下载进度？
A: 运行以下命令查看任务状态：
```bash
ps aux | grep modelscope
ps aux | grep download_mfa
```

### Q: Qwen3-TTS 下载失败怎么办？
A: 重新运行下载命令：
```bash
rm -rf ./models/Qwen3-TTS-12Hz-1.7B-Base
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base --local_dir ./models/Qwen3-TTS-12Hz-1.7B-Base
```

### Q: MFA 对齐总是失败？
A: API 会自动降级到均匀时间分配，仍能正常工作。如果需要精确对齐：
```bash
python /tmp/download_mfa_models.py  # 重新尝试下载 MFA 模型
```

### Q: 如何清理下载缓存？
A: 清理临时文件：
```bash
rm -rf ~/.cache/huggingface/
rm -rf ./models/*/._*
rm -rf ./models/*/.cache/
```

## 下一步

1. **等待下载完成** (15-40 分钟)
2. **运行验证脚本**:
   ```bash
   python verify_installation.py
   ```
3. **启动 API 服务**:
   ```bash
   python app.py
   ```
4. **访问 API 文档**:
   http://localhost:8000/docs

---

**更新时间**: 2026-01-27
**项目**: yuhuo-tts (TTS-Alignment-API)
