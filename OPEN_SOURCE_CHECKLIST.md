# Open Source Checklist

公开仓库前，至少确认下面几项：

- 选择并添加顶层 `LICENSE`
- 检查所有提交历史里是否出现过真实密钥、Token、私有域名或内部路径
- 确认 `.env`、`.env.cloud`、`models/`、`third_party/` 没有被跟踪
- 确认 `logs/`、`temp_audio/`、`output_audio/` 只有 `.gitkeep`
- 核对 CosyVoice2、Qwen3-TTS、MFA 和模型权重的许可证
- 在全新环境用 `install.sh` 或 Docker 跑通一次
- 如需对外服务，补充鉴权、限流和审计日志

建议额外检查：

- `git log --stat -- .env .env.cloud`
- `git grep -nE "(AKIA|sk-|token|secret|password|PRIVATE KEY)"`
- `git ls-files | rg "^(models|third_party|venv|logs|temp_audio|output_audio)/"`
