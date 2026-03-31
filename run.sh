#!/bin/bash

# TTS-Alignment-API 启动脚本
# 此脚本正确设置 PYTHONPATH 并启动应用

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 激活虚拟环境
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "❌ 虚拟环境未找到: $SCRIPT_DIR/venv"
    echo "请先运行: bash install.sh"
    exit 1
fi

# 设置 PYTHONPATH（关键！）
# 必须包含 CosyVoice 项目中的 Matcha-TTS 模块
export PYTHONPATH="$SCRIPT_DIR/third_party/CosyVoice:$SCRIPT_DIR/third_party/CosyVoice/third_party/Matcha-TTS:$PYTHONPATH"

echo "✓ PYTHONPATH 已设置："
echo "  $PYTHONPATH"
echo ""

# 验证环境
python -c "from cosyvoice.cli.cosyvoice import CosyVoice; print('✓ CosyVoice 环境检查通过')" || {
    echo "❌ CosyVoice 环境检查失败"
    echo "请确保已运行以下步骤："
    echo "  1. bash install.sh（安装脚本）"
    echo "  2. 检查 third_party/CosyVoice 目录是否存在"
    exit 1
}

echo ""
echo "🚀 启动 TTS-Alignment-API..."
echo "   访问 API 文档: http://0.0.0.0:8000/docs"
echo ""

# 启动应用
uvicorn app:app --host 0.0.0.0 --port 8000 "$@"
