#!/bin/bash

# 检查后台下载任务状态

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

echo "=========================================="
echo "📥 TTS-Alignment-API 下载进度检查"
echo "=========================================="
echo ""

# 检查 Qwen3-TTS 下载
echo "1️⃣  Qwen3-TTS 模型下载"
if pgrep -f "modelscope download.*Qwen3-TTS" > /dev/null; then
    echo "   ⏳ 进行中..."
    if [ -d "./models/Qwen3-TTS-12Hz-1.7B-Base" ]; then
        size=$(du -sh ./models/Qwen3-TTS-12Hz-1.7B-Base 2>/dev/null | cut -f1)
        echo "   📊 当前大小: $size"
    fi
else
    if [ -d "./models/Qwen3-TTS-12Hz-1.7B-Base" ]; then
        size=$(du -sh ./models/Qwen3-TTS-12Hz-1.7B-Base 2>/dev/null | cut -f1)
        files=$(find ./models/Qwen3-TTS-12Hz-1.7B-Base -type f | wc -l)
        echo "   ✅ 已完成"
        echo "   📊 大小: $size"
        echo "   📁 文件数: $files"
    else
        echo "   ❌ 尚未开始"
    fi
fi
echo ""

# 检查 MFA 模型下载
echo "2️⃣  MFA 模型下载"
if pgrep -f "download_mfa" > /dev/null; then
    echo "   ⏳ 进行中..."
else
    if [ -d ~/.mfa/models ]; then
        models=$(find ~/.mfa/models -type d -maxdepth 2 | wc -l)
        echo "   ✅ 已完成"
        echo "   📁 模型数: $models"
    else
        echo "   ❌ 尚未开始"
    fi
fi
echo ""

# 检查模型完整性
echo "3️⃣  模型文件检查"
echo ""

echo "   CosyVoice2:"
if [ -f "./models/CosyVoice2-0.5B/llm.pt" ]; then
    size=$(du -sh ./models/CosyVoice2-0.5B/llm.pt | cut -f1)
    echo "   ✅ llm.pt ($size)"
else
    echo "   ❌ llm.pt 缺失"
fi

echo ""
echo "   Qwen3-TTS:"
if [ -f "./models/Qwen3-TTS-12Hz-1.7B-Base/speech_tokenizer/model.safetensors" ]; then
    size=$(du -sh ./models/Qwen3-TTS-12Hz-1.7B-Base/speech_tokenizer/model.safetensors | cut -f1)
    echo "   ✅ speech_tokenizer/model.safetensors ($size)"
else
    echo "   ❌ speech_tokenizer/model.safetensors 缺失"
fi

if [ -f "./models/Qwen3-TTS-12Hz-1.7B-Base/config.json" ]; then
    echo "   ✅ config.json"
else
    echo "   ❌ config.json 缺失"
fi
echo ""

echo "=========================================="
echo "📋 建议:"
echo "=========================================="

# 检查是否可以启动
ready=true

if [ ! -f "./models/CosyVoice2-0.5B/llm.pt" ]; then
    echo "❌ CosyVoice2 不完整"
    ready=false
fi

if [ ! -f "./models/Qwen3-TTS-12Hz-1.7B-Base/config.json" ]; then
    echo "❌ Qwen3-TTS 不完整"
    ready=false
fi

if [ "$ready" = true ]; then
    echo "✅ 模型文件完整，可以启动服务"
    echo ""
    echo "运行:"
    echo "  python app.py"
else
    echo "⏳ 等待模型下载完成..."
    echo ""
    echo "重新运行此脚本检查进度:"
    echo "  bash scripts/check_download_status.sh"
fi

echo ""
