#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "❌ 未找到 uv，请先安装 uv"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MFA 安装与验收"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "1. 同步项目依赖"
uv sync

echo ""
echo "2. 检查 MFA CLI"
if uv run mfa --version >/dev/null 2>&1; then
    echo "✅ MFA CLI 可用（来自项目 uv 环境）"
else
    echo "❌ MFA CLI 不可用"
    echo ""
    echo "请先安装 MFA，可选方式："
    echo "  conda install -c conda-forge montreal-forced-aligner -y"
    echo "或确认 uv sync 没有失败，再重新执行本脚本。"
    exit 1
fi

echo ""
echo "3. 下载中文模型"
uv run mfa model download acoustic mandarin_mfa
uv run mfa model download dictionary mandarin_mfa

echo ""
echo "4. 检查中文分词依赖"
uv run python -c "import spacy_pkuseg, dragonmapper, hanziconv" >/dev/null 2>&1
echo "✅ 中文分词依赖可用"

echo ""
echo "5. 验收状态"
uv run python scripts/check_mfa_ready.py

echo ""
echo "6. 运行中文对齐测试"
uv run python scripts/test_mfa_chinese.py
