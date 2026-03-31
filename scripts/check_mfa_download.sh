#!/bin/bash

# 检查 MFA 中文模型下载进度

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

echo ""
echo "=========================================="
echo "📥 MFA 中文模型下载监控"
echo "=========================================="
echo ""

# 检查是否有下载进程在运行
if pgrep -f "modelscope download" > /dev/null; then
    echo "⏳ 下载进行中..."
    ps aux | grep modelscope | grep -v grep
    echo ""
else
    echo "✅ 下载进程已结束"
    echo ""
fi

# 检查声学模型
echo "1️⃣  声学模型（Acoustic Model）"
acoustic_dir="$HOME/.mfa/models/acoustic_models/mandarin_flac"
if [ -d "$acoustic_dir" ]; then
    file_count=$(find "$acoustic_dir" -type f 2>/dev/null | wc -l)
    if [ "$file_count" -gt 0 ]; then
        size=$(du -sh "$acoustic_dir" 2>/dev/null | cut -f1)
        echo "   ✅ 已下载"
        echo "   📁 位置: $acoustic_dir"
        echo "   📊 大小: $size"
        echo "   📄 文件数: $file_count"
    else
        echo "   ⏳ 目录存在但为空（下载中...）"
    fi
else
    echo "   ❌ 目录不存在"
fi
echo ""

# 检查词典
echo "2️⃣  发音词典（Dictionary）"
dict_dir="$HOME/.mfa/models/g2p_models/mandarin_flac"
if [ -d "$dict_dir" ]; then
    file_count=$(find "$dict_dir" -type f 2>/dev/null | wc -l)
    if [ "$file_count" -gt 0 ]; then
        size=$(du -sh "$dict_dir" 2>/dev/null | cut -f1)
        echo "   ✅ 已下载"
        echo "   📁 位置: $dict_dir"
        echo "   📊 大小: $size"
        echo "   📄 文件数: $file_count"
    else
        echo "   ⏳ 目录存在但为空（下载中...）"
    fi
else
    echo "   ❌ 目录不存在"
fi
echo ""

# 检查是否都完成
echo "=========================================="
if [ -f "$acoustic_dir/final.mdl" ] || [ -f "$acoustic_dir"/*.mdl ] || [ "$(find "$acoustic_dir" -type f 2>/dev/null | wc -l)" -gt 0 ]; then
    if [ -f "$dict_dir/lexicon.txt" ] || [ "$(find "$dict_dir" -type f 2>/dev/null | wc -l)" -gt 0 ]; then
        echo "✅ 所有模型已下载完成！"
        echo ""
        echo "下一步："
        echo "1. 运行测试脚本: python scripts/test_mfa_chinese.py"
        echo "2. 启动 API 服务: python app.py"
        echo ""
        exit 0
    fi
fi

echo "⏳ 下载进行中，请稍候..."
echo ""
echo "提示："
echo "- 声学模型: 约 250-300MB"
echo "- 词典: 约 10-20MB"
echo "- 总耗时: 通常 5-15 分钟"
echo ""
echo "重新检查: bash scripts/check_mfa_download.sh"
echo ""

exit 1
