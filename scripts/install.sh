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
PYTHON_VERSION="3.10"
VENV_DIR="venv"
MODELS_DIR="$PROJECT_DIR/models"
TEMP_DIR="/tmp/tts-downloads"

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
# Step 2: 创建虚拟环境
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: 创建虚拟环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -d "$VENV_DIR" ]; then
    warning "虚拟环境已存在，跳过创建"
else
    echo "创建虚拟环境..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    success "虚拟环境创建完成"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
. "$VENV_DIR/bin/activate"
success "虚拟环境已激活"

# ============================================================
# Step 3: 升级 pip
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: 升级 pip"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "升级 pip..."
pip install --upgrade pip setuptools wheel
success "pip 升级完成"

# ============================================================
# Step 4: 安装 Python 依赖
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: 安装 Python 依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "安装依赖包（这可能需要 5-10 分钟）..."
pip install -r requirements.txt

success "Python 依赖安装完成"

echo "安装 Qwen3-TTS Python 包..."
pip install git+https://github.com/QwenLM/Qwen3-TTS.git
success "Qwen3-TTS Python 包安装完成"

# ============================================================
# Step 5: 创建目录结构
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
# Step 5.2: 克隆 CosyVoice 官方仓库
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

    # 安装 CosyVoice 的依赖
    echo "安装 CosyVoice 依赖..."
    if [ -f "third_party/CosyVoice/requirements.txt" ]; then
        pip install -r third_party/CosyVoice/requirements.txt
        success "CosyVoice 依赖安装完成"
    else
        warning "找不到 CosyVoice requirements.txt"
    fi
fi

# ============================================================
# Step 6: 下载 TTS 模型
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: 下载 TTS 模型"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查 modelscope
if ! command_exists modelscope; then
    echo "安装 modelscope..."
    pip install modelscope
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
# Step 7: 下载 MFA 模型
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: 下载 MFA 模型"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 初始化 conda（如果已安装）
if command_exists conda; then
    echo "使用 conda 来确保 MFA 完整安装..."
    conda install -c conda-forge montreal-forced-aligner -y
else
    echo "未检测到 conda，MFA 通过 pip 已安装"
fi

# 下载 MFA 模型（需要 MFA 环境）
echo ""
echo "📥 下载 MFA 中文模型 (mandarin_mfa)..."
if command_exists mfa; then
    mfa model download acoustic mandarin_mfa || warning "声学模型下载可能失败"
    mfa model download dictionary mandarin_mfa || warning "词典下载可能失败"
    success "MFA 模型配置完成"
else
    warning "MFA 命令未找到，跳过模型下载"
    warning "可稍后手动运行: mfa model download acoustic mandarin_mfa"
fi

# ============================================================
# Step 8: 验证安装
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
if python -c "import torch; import fastapi; import librosa" 2>/dev/null; then
    success "Python 依赖 ✅"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    warning "Python 依赖可能不完整"
fi

echo ""
echo "验证结果: $CHECKS_PASSED / $CHECKS_TOTAL 通过"
echo ""

# ============================================================
# Step 9: 清理临时文件
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
echo "  - 虚拟环境: $PROJECT_DIR/$VENV_DIR"
echo "  - Python 依赖: 已安装"
echo "  - CosyVoice2 模型: $MODELS_DIR/CosyVoice2-0.5B (4.1GB) - iic/CosyVoice2-0.5B"
echo "  - Qwen3-TTS 模型: $MODELS_DIR/Qwen3-TTS-12Hz-1.7B-Base (4.2GB) - Qwen/Qwen3-TTS-12Hz-1.7B-Base"
echo "  - MFA 模型: ~/.mfa/models/ (约 100MB)"
echo ""

echo "🚀 快速开始："
echo ""
echo "  # 激活虚拟环境"
echo "  source venv/bin/activate"
echo ""
echo "  # 启动 API 服务"
echo "  python app.py"
echo ""
echo "  # 或使用 uvicorn（生产环境）"
echo "  uvicorn app:app --host 0.0.0.0 --port 8000"
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
