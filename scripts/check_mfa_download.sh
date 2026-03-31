#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

echo ""
echo "=========================================="
echo "📥 MFA 状态检查"
echo "=========================================="
echo ""

if pgrep -f "modelscope download" > /dev/null; then
    echo "⏳ 检测到 modelscope 下载进程："
    ps aux | grep modelscope | grep -v grep || true
    echo ""
fi

python3 scripts/check_mfa_ready.py || {
    echo ""
    echo "⚠️  MFA 尚未 ready。"
    echo "建议下一步："
    echo "1. 确认 mfa 命令可执行"
    echo "2. 下载或检查声学模型与词典"
    echo "3. 运行: python3 scripts/test_mfa_chinese.py"
    exit 1
}

echo ""
echo "✅ MFA 已 ready"
echo "下一步："
echo "1. 运行测试脚本: python3 scripts/test_mfa_chinese.py"
echo "2. 启动 API 服务: bash scripts/run.sh"
