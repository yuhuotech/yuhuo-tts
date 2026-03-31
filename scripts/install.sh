#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

MODELS_DIR="$PROJECT_DIR/models"
COSYVOICE_ROOT="$PROJECT_DIR/third_party/CosyVoice"
ENV_FILE="$PROJECT_DIR/.env"
ENV_EXAMPLE="$PROJECT_DIR/.env.example"
OS_NAME="$(uname -s)"
DISTRO_ID=""

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

green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[1;33m%s\033[0m\n' "$1"; }
red() { printf '\033[0;31m%s\033[0m\n' "$1"; }
die() { red "❌ $1"; exit 1; }

need_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "未找到 $1，请先安装"
}

detect_linux_distro() {
    if [ "$OS_NAME" != "Linux" ]; then
        return
    fi
    if [ -f /etc/os-release ]; then
        DISTRO_ID="$(. /etc/os-release && printf '%s' "${ID:-}")"
    fi
}

print_linux_hints() {
    if [ "$OS_NAME" != "Linux" ]; then
        return
    fi

    case "$DISTRO_ID" in
        ubuntu|debian)
            echo "检测到 Linux 发行版: ${DISTRO_ID:-unknown}"
            echo "如缺系统依赖，可先执行："
            echo "  sudo apt update"
            echo "  sudo apt install -y git curl build-essential ffmpeg"
            ;;
        centos|rhel|rocky|almalinux)
            echo "检测到 Linux 发行版: ${DISTRO_ID:-unknown}"
            echo "如缺系统依赖，可先执行："
            echo "  sudo yum install -y git curl gcc gcc-c++ make ffmpeg"
            echo "或较新系统使用："
            echo "  sudo dnf install -y git curl gcc gcc-c++ make ffmpeg"
            ;;
        *)
            echo "检测到 Linux 系统"
            echo "请确保已安装 git、curl、编译工具链和 ffmpeg"
            ;;
    esac
    echo ""
}

ensure_uv() {
    if command -v uv >/dev/null 2>&1; then
        return
    fi

    command -v curl >/dev/null 2>&1 || die "未找到 uv，且无法自动安装，因为缺少 curl"

    echo "未找到 uv，尝试自动安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    if [ -x "$HOME/.local/bin/uv" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi

    command -v uv >/dev/null 2>&1 || die "uv 自动安装失败，请手动安装后重试"
}

read_env_value() {
    local key="$1"
    local file="$2"
    local line
    line="$(grep -E "^${key}=" "$file" | tail -n 1 || true)"
    if [ -z "$line" ]; then
        return 1
    fi
    printf '%s' "${line#*=}"
}

download_model() {
    local model_name="$1"
    local local_dir="$2"
    local marker="$3"

    if [ -f "$local_dir/$marker" ]; then
        green "✅ 模型已存在: $local_dir"
        return
    fi

    echo "📥 下载模型: $model_name"
    uv run modelscope download --model "$model_name" --local_dir "$local_dir"
    [ -f "$local_dir/$marker" ] || die "模型下载失败: $model_name"
    green "✅ 模型下载完成: $model_name"
}

echo ""
echo "YuHuo TTS 一键安装"
echo ""

detect_linux_distro
print_linux_hints

need_cmd python3
need_cmd git
ensure_uv

[ -f "$ENV_FILE" ] || cp "$ENV_EXAMPLE" "$ENV_FILE"

DEFAULT_TTS_MODEL="$(read_env_value DEFAULT_TTS_MODEL "$ENV_FILE" || true)"
MFA_ENABLE_VALUE="$(read_env_value MFA_ENABLE "$ENV_FILE" || true)"

[ -n "$DEFAULT_TTS_MODEL" ] || DEFAULT_TTS_MODEL="cosyvoice2"
[ -n "$MFA_ENABLE_VALUE" ] || MFA_ENABLE_VALUE="True"

mkdir -p "$MODELS_DIR" temp_audio output_audio logs third_party

echo "1. 同步 Python 依赖"
uv sync

echo ""
echo "2. 准备 CosyVoice 源码"
if [ -d "$COSYVOICE_ROOT" ]; then
    green "✅ 已存在: $COSYVOICE_ROOT"
else
    git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git "$COSYVOICE_ROOT"
    green "✅ CosyVoice 克隆完成"
fi

echo ""
echo "3. 安装 CosyVoice 运行时依赖"
uv pip install --no-build-isolation "${COSYVOICE_RUNTIME_DEPS[@]}"
green "✅ CosyVoice 运行时依赖已安装"

echo ""
echo "4. 下载默认模型"
case "$DEFAULT_TTS_MODEL" in
    cosyvoice2)
        download_model "iic/CosyVoice2-0.5B" "$MODELS_DIR/CosyVoice2-0.5B" "llm.pt"
        ;;
    qwen3)
        download_model "Qwen/Qwen3-TTS-12Hz-1.7B-Base" "$MODELS_DIR/Qwen3-TTS-12Hz-1.7B-Base" "model.safetensors"
        ;;
    *)
        die "不支持的 DEFAULT_TTS_MODEL: $DEFAULT_TTS_MODEL"
        ;;
esac

echo ""
echo "5. 安装 MFA"
if [ "$MFA_ENABLE_VALUE" = "True" ]; then
    if bash scripts/install_mfa.sh; then
        green "✅ MFA 已就绪"
    else
        yellow "⚠️  MFA 安装未通过，服务仍可启动，但可能不返回精准时间戳"
    fi
else
    yellow "⚠️  MFA_ENABLE=False，跳过 MFA 安装"
fi

echo ""
echo "6. 验收安装"
uv run python scripts/verify_installation.py || yellow "⚠️  安装检查未全部通过，请按输出处理"

echo ""
green "✅ 安装完成"
echo "配置文件: $ENV_FILE"
echo "默认模型: $DEFAULT_TTS_MODEL"
echo ""
echo "启动命令:"
echo "  bash scripts/run.sh"
echo ""
echo "接口文档:"
echo "  http://127.0.0.1:8000/docs"
