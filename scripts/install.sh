#!/bin/bash

# TTS-Alignment-API 完整安装脚本
# 用于 Linux 服务器部署
# 使用方法: bash scripts/install.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       🚀 TTS-Alignment-API 完整安装脚本                        ║"
echo "║                                                                ║"
echo "║       该脚本将自动安装所有依赖和模型                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 配置
MODELS_DIR="$PROJECT_DIR/models"
TEMP_DIR="/tmp/tts-downloads"
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

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印成功消息
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 函数：打印错误消息
error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# 函数：打印警告消息
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 函数：检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================
# Step 1: 检查系统依赖
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: 检查系统依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查 Python
if command_exists python3; then
    PYTHON_CMD="python3"
    PYTHON_VER=$($PYTHON_CMD --version | cut -d' ' -f2)
    success "Python $PYTHON_VER 已安装"
else
    error "Python3 未找到，请先安装 Python 3.10+"
fi

# 检查 pip
if command_exists pip3; then
    success "pip3 已安装"
else
    error "pip3 未找到，请先安装"
fi

# 检查 git（可选）
if command_exists git; then
    success "git 已安装"
else
    warning "git 未安装（可选）"
fi

# ============================================================
# Step 2: 检查 uv
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: 检查 uv"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command_exists uv; then
    success "uv 已安装"
else
    error "未找到 uv，请先安装 uv: https://docs.astral.sh/uv/"
fi

# ============================================================
# Step 3: 创建目录结构
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: 创建目录结构"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

mkdir -p "$MODELS_DIR"
mkdir -p temp_audio
mkdir -p output_audio
mkdir -p logs
mkdir -p "$TEMP_DIR"
mkdir -p third_party

success "目录结构创建完成"

# ============================================================
# Step 3.2: 克隆 CosyVoice 官方仓库
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5.2: 克隆 CosyVoice 官方仓库"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -d "third_party/CosyVoice" ]; then
    warning "CosyVoice 仓库已存在，跳过克隆"
else
    echo "克隆官方 CosyVoice 仓库（包含子模块）..."
    # 重要：必须添加 --recursive 参数以下载 Matcha-TTS 子模块
    if git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git third_party/CosyVoice; then
        success "CosyVoice 仓库克隆完成"
    else
        # 如果克隆失败，尝试分步进行
        echo "尝试分步克隆..."
        if git clone https://github.com/FunAudioLLM/CosyVoice.git third_party/CosyVoice; then
            cd third_party/CosyVoice
            git submodule update --init --recursive
            cd ../../
            success "CosyVoice 仓库克隆完成（通过分步方式）"
        else
            error "CosyVoice 仓库克隆失败"
        fi
    fi

fi

# ============================================================
# Step 4: 使用 uv 同步 Python 依赖
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: 使用 uv 同步 Python 依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "同步项目依赖（这可能需要 5-10 分钟）..."
uv sync

if [ -f "third_party/CosyVoice/requirements.txt" ]; then
    echo "同步 CosyVoice 依赖..."
    uv pip install --no-build-isolation "${COSYVOICE_RUNTIME_DEPS[@]}"
    success "CosyVoice 依赖安装完成"
else
    warning "找不到 CosyVoice requirements.txt"
fi

if uv run python -c "import spacy_pkuseg, dragonmapper, hanziconv" >/dev/null 2>&1; then
    success "MFA 中文分词依赖已安装"
else
    warning "MFA 中文分词依赖缺失，重新执行 uv sync 或 bash scripts/install_mfa.sh"
fi

# ============================================================
# Step 5: 下载 TTS 模型
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: 下载 TTS 模型"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查 modelscope
if ! command_exists modelscope; then
    echo "安装 modelscope..."
    uv pip install modelscope
fi

# 下载 CosyVoice2
echo ""
echo "📥 下载 CosyVoice2-0.5B (约 4.1GB)..."
modelscope download --model iic/CosyVoice2-0.5B \
    --local_dir "$MODELS_DIR/CosyVoice2-0.5B"

if [ -f "$MODELS_DIR/CosyVoice2-0.5B/llm.pt" ]; then
    success "CosyVoice2 下载完成"
else
    error "CosyVoice2 下载失败"
fi

# 下载 Qwen3-TTS
echo ""
echo "📥 下载 Qwen3-TTS-12Hz-1.7B-Base (约 4.2GB)..."
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
    --local_dir "$MODELS_DIR/Qwen3-TTS-12Hz-1.7B-Base"

if [ -f "$MODELS_DIR/Qwen3-TTS-12Hz-1.7B-Base/model.safetensors" ]; then
    success "Qwen3-TTS 下载完成"
else
    error "Qwen3-TTS 下载失败"
fi

# ============================================================
# Step 6: 下载 MFA 模型
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: 下载 MFA 模型"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "检查 uv 环境中的 MFA CLI..."
if uv run mfa --version >/dev/null 2>&1; then
    success "MFA CLI 已安装"
    echo ""
    echo "📥 下载 MFA 中文模型 (mandarin_mfa)..."
    uv run mfa model download acoustic mandarin_mfa || warning "声学模型下载可能失败"
    uv run mfa model download dictionary mandarin_mfa || warning "词典下载可能失败"
    success "MFA 模型配置完成"
else
    warning "uv 环境中的 MFA CLI 不可用"
    warning "可稍后运行: bash scripts/install_mfa.sh"
fi

# ============================================================
# Step 7: 验证安装
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: 验证安装"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "验证模型文件..."
CHECKS_PASSED=0
CHECKS_TOTAL=0

# 检查 CosyVoice2
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -f "$MODELS_DIR/CosyVoice2-0.5B/llm.pt" ]; then
    success "CosyVoice2 模型 ✅"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    error "CosyVoice2 模型 ❌"
fi

# 检查 Qwen3-TTS
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -f "$MODELS_DIR/Qwen3-TTS-12Hz-1.7B-Base/model.safetensors" ]; then
    success "Qwen3-TTS 模型 ✅"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    error "Qwen3-TTS 模型 ❌"
fi

# 检查 Python 依赖
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if uv run python -c "import torch; import fastapi; import librosa" 2>/dev/null; then
    success "Python 依赖 ✅"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    warning "Python 依赖可能不完整"
fi

echo ""
echo "验证结果: $CHECKS_PASSED / $CHECKS_TOTAL 通过"
echo ""

echo "MFA 状态检查..."
if uv run python scripts/check_mfa_ready.py; then
    success "MFA 验收通过"
else
    warning "MFA 尚未 ready，可稍后运行: bash scripts/install_mfa.sh"
fi

# ============================================================
# Step 8: 清理临时文件
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 9: 清理临时文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

rm -rf "$TEMP_DIR"
success "临时文件清理完成"

# ============================================================
# 完成
# ============================================================
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ 安装完成！                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 安装摘要："
echo "  - uv 项目环境: $PROJECT_DIR/.venv"
echo "  - Python 依赖: 已安装"
echo "  - CosyVoice2 模型: $MODELS_DIR/CosyVoice2-0.5B (4.1GB) - iic/CosyVoice2-0.5B"
echo "  - Qwen3-TTS 模型: $MODELS_DIR/Qwen3-TTS-12Hz-1.7B-Base (4.2GB) - Qwen/Qwen3-TTS-12Hz-1.7B-Base"
echo "  - MFA 模型: ~/.mfa/models/ (约 100MB)"
echo ""

echo "🚀 快速开始："
echo ""
echo "  # 同步依赖"
echo "  uv sync"
echo ""
echo "  # 启动 API 服务"
echo "  bash scripts/run.sh"
echo ""
echo "  # 或直接使用 uv"
echo "  uv run uvicorn app:app --host 0.0.0.0 --port 8000"
echo ""

echo "📖 访问 API 文档:"
echo "  http://localhost:8000/docs"
echo ""

echo "⚙️  配置文件:"
echo "  - .env - 环境变量配置"
echo "  - config.py - Python 配置"
echo ""

echo "✅ 安装成功！现在可以启动服务了。"
echo ""
