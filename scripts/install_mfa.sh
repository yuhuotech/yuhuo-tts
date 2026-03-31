#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

MFA_CMD=""

find_mfa_command() {
    if uv run mfa version >/dev/null 2>&1; then
        MFA_CMD="uv run mfa"
        return 0
    fi
    if command -v mfa >/dev/null 2>&1 && mfa version >/dev/null 2>&1; then
        MFA_CMD="mfa"
        return 0
    fi
    return 1
}

if ! command -v uv >/dev/null 2>&1; then
    echo "❌ 未找到 uv，请先安装 uv"
    exit 1
fi

echo "MFA 安装与验收"
echo ""

echo "1. 同步项目依赖"
uv sync

echo ""
echo "2. 检查 MFA CLI"
if find_mfa_command; then
    echo "✅ MFA CLI 可用"
    echo "   使用命令: $MFA_CMD"
else
    echo "❌ MFA CLI 不可用"
    echo ""
    echo "请先安装 MFA。推荐方式："
    echo "  conda install -c conda-forge montreal-forced-aligner -y"
    echo ""
    echo "Ubuntu 可先准备基础工具："
    echo "  sudo apt update && sudo apt install -y git curl build-essential ffmpeg"
    echo "CentOS/RHEL 可先准备基础工具："
    echo "  sudo yum install -y git curl gcc gcc-c++ make ffmpeg"
    exit 1
fi

echo ""
echo "3. 下载中文模型"
$MFA_CMD model download acoustic mandarin_mfa
$MFA_CMD model download dictionary mandarin_mfa

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
