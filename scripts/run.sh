#!/bin/bash

set -euo pipefail

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

command -v uv >/dev/null 2>&1 || { echo "❌ 未找到 uv"; exit 1; }

if [ ! -d "$COSYVOICE_ROOT" ]; then
    echo "❌ 未找到 CosyVoice 源码目录: $COSYVOICE_ROOT"
    echo "请先运行: bash scripts/install.sh"
    exit 1
fi

export PYTHONPATH="$COSYVOICE_ROOT:$MATCHA_ROOT:${PYTHONPATH:-}"

cd "$PROJECT_DIR"

uv sync

if ! uv run python -c "from cosyvoice.cli.cosyvoice import AutoModel" >/dev/null 2>&1; then
    uv pip install --no-build-isolation "${COSYVOICE_RUNTIME_DEPS[@]}"
fi

echo "启动服务: http://127.0.0.1:8000/docs"

exec uv run uvicorn app:app --host 0.0.0.0 --port 8000 "$@"
