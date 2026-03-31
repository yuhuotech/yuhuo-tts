# MFA 中文模型设置指南

## 推荐流程

项目现在默认走 `uv`。如果你要启用真实 MFA 对齐，直接执行：

```bash
bash scripts/install_mfa.sh
```

这个脚本会完成：

- `uv sync`
- 检查项目环境中的 MFA CLI
- 下载 `mandarin_mfa` 声学模型和词典
- 检查 `spacy-pkuseg`、`dragonmapper`、`hanziconv`
- 运行 `scripts/check_mfa_ready.py`
- 运行 `scripts/test_mfa_chinese.py`

## 手动步骤

如果你想手动执行，顺序如下：

```bash
uv sync
uv run mfa --version
uv run mfa model download acoustic mandarin_mfa
uv run mfa model download dictionary mandarin_mfa
uv run python scripts/check_mfa_ready.py
uv run python scripts/test_mfa_chinese.py
```

## 验收标准

`uv run python scripts/check_mfa_ready.py` 至少应显示：

```text
available: True
command_available: True
command_path: .../mfa
acoustic_model: mandarin_mfa
dictionary: mandarin_mfa
reason: ready
```

`uv run python scripts/test_mfa_chinese.py` 应能完成 TextGrid 生成和解析。

## 启动服务

MFA 验收通过后，使用：

```bash
bash scripts/run.sh
```

服务健康检查会在 `/health` 返回 `mfa_status`，包含：

- `available`
- `command_available`
- `command_path`
- `acoustic_model_path`
- `dictionary_path`
- `fallback_alignment`
- `reason`

## 常见问题

### `mfa command missing`

优先执行：

```bash
bash scripts/install_mfa.sh
```

如果仍失败，检查：

```bash
uv run mfa --version
uv run python scripts/check_mfa_ready.py
```

### 没有 MFA 时是否返回时间戳

由 `MFA_FALLBACK_ALIGNMENT` 控制：

- `none`: 不返回时间戳
- `uniform`: 返回均分时间戳

默认是 `none`。

### 模型放在哪里

项目会自动识别这几类常见位置：

- `~/.mfa/models/acoustic_models/...`
- `~/.mfa/models/dictionary_models/...`
- `~/Documents/MFA/pretrained_models/...`

- [ ] 下载任务已启动
- [ ] 已运行 `bash scripts/check_mfa_download.sh` 验证下载
- [ ] 已运行 `python scripts/test_mfa_chinese.py` 测试对齐
- [ ] 测试通过显示 "✅ MFA 中文模型已准备就绪"
- [ ] 所有 TTS 模型已完整（CosyVoice2 + Qwen3-TTS）
- [ ] Python 依赖已安装 (`pip install -r requirements.txt`)
- [ ] 可以启动 API 服务

---

## 📞 需要帮助？

```bash
# 查看详细日志
tail -f logs/app.log

# 运行完整的验证
python scripts/verify_installation.py

# 查看 MFA 模型详情
python3 << 'EOF'
from pathlib import Path
acoustic = Path.home() / '.mfa/models/acoustic_models/mandarin_flac'
dict_dir = Path.home() / '.mfa/models/g2p_models/mandarin_flac'
print("声学模型:", list(acoustic.glob('*')))
print("词典:", list(dict_dir.glob('*')))
EOF
```

---

**准备就绪后，就可以享受精确的中文字级时间戳了！** 🎉
