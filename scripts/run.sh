#!/bin/bash

set -euo pipefail

# TTS-Alignment-API 启动脚本
# 使用 uv 管理环境并启动应用

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
COSYVOICE_ROOT="$PROJECT_DIR/third_party/CosyVoice"
MATCHA_ROOT="$COSYVOICE_ROOT/third_party/Matcha-TTS"
COSYVOICE_RUNTIME_DEPS=(
    "HyperPyYAML==1.2.3"
    "hydra-core==1.3.2"
    "omegaconf==2.3.0"
    "inflect==7.3.1"
    "wetext==0.0.4"
    "conformer==0.3.2"
    "diffusers==0.29.0"
    "gdown==5.1.0"
    "x-transformers==2.11.24"
    "lightning==2.2.4"
    "openai-whisper==20231117"
    "protobuf==4.25.0"
    "pyarrow==18.1.0"
    "rich==13.7.1"
    "wget==3.2"
)

if ! command -v uv >/dev/null 2>&1; then
    echo "❌ 未找到 uv，请先安装 uv"
    exit 1
fi

if [ ! -d "$COSYVOICE_ROOT" ]; then
    echo "❌ 未找到 CosyVoice 源码目录: $COSYVOICE_ROOT"
    echo "请先运行: bash scripts/install.sh"
    exit 1
fi

export PYTHONPATH="$COSYVOICE_ROOT:$MATCHA_ROOT:${PYTHONPATH:-}"

echo "✓ PYTHONPATH 已设置："
echo "  $PYTHONPATH"
echo ""

cd "$PROJECT_DIR"

echo "🔄 使用 uv 同步依赖..."
uv sync

if ! uv run python -c "from cosyvoice.cli.cosyvoice import AutoModel" >/dev/null 2>&1; then
    echo ""
    echo "🔄 检测到 CosyVoice 依赖未就绪，使用 uv 补装第三方依赖..."
    uv pip install --no-build-isolation "${COSYVOICE_RUNTIME_DEPS[@]}"
fi

echo ""
echo "🚀 启动 TTS-Alignment-API..."
echo "   访问 API 文档: http://0.0.0.0:8000/docs"
echo ""

exec uv run uvicorn app:app --host 0.0.0.0 --port 8000 "$@"
