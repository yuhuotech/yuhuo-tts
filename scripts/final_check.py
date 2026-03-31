#!/usr/bin/env python3
"""
最终完整性检查 - 确保所有模型和配置都就绪
"""

import os
import sys
from pathlib import Path
import importlib.util

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from alignment.mfa_aligner import MFAAligner


def _resolve_existing_path(*candidates: Path) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _path_size_mb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / (1024**2)
    return sum(item.stat().st_size for item in path.rglob('*') if item.is_file()) / (1024**2)

def check_tts_models():
    """检查 TTS 模型"""
    print("=" * 60)
    print("📦 TTS 模型检查")
    print("=" * 60)

    models = {
        'CosyVoice2-0.5B': [
            'llm.pt',
            'flow.pt',
            'hift.pt',
            'speech_tokenizer_v2.onnx',
        ],
        'Qwen3-TTS-12Hz-1.7B-Base': [
            'model.safetensors',
            'config.json',
        ]
    }

    base_path = PROJECT_ROOT / 'models'
    all_ok = True

    for model, files in models.items():
        model_path = base_path / model
        print(f"\n{model}:")

        if not model_path.exists():
            print(f"  ❌ 目录不存在: {model_path}")
            all_ok = False
            continue

        missing = []
        for f in files:
            if not (model_path / f).exists():
                missing.append(f)

        if missing:
            print(f"  ❌ 缺失文件: {missing}")
            all_ok = False
        else:
            size_gb = sum(
                (model_path / f).stat().st_size
                for f in files if (model_path / f).exists()
            ) / (1024**3)
            print(f"  ✅ 完整 ({size_gb:.1f}GB)")

    return all_ok

def check_mfa_models():
    """检查 MFA 模型"""
    print("\n" + "=" * 60)
    print("🔤 MFA 中文模型检查")
    print("=" * 60)
    status = MFAAligner().get_status(force_refresh=True)
    print(f"enabled: {status['enabled']}")
    print(f"available: {status['available']}")
    print(f"command_available: {status['command_available']}")
    print(f"command_path: {status['command_path']}")
    print(f"command_error: {status['command_error']}")
    print(f"fallback_alignment: {status['fallback_alignment']}")
    print(f"reason: {status['reason']}")
    print(f"\n声学模型 ({status['acoustic_model']}):")
    if status["acoustic_model_path"]:
        path = Path(status["acoustic_model_path"])
        print(f"  ✅ {path}")
        print(f"  📊 大小: {_path_size_mb(path):.1f}MB")
    else:
        print(f"  ❌ 未找到: {status['acoustic_model']}")

    print(f"\n词典 ({status['dictionary']}):")
    if status["dictionary_path"]:
        path = Path(status["dictionary_path"])
        print(f"  ✅ {path}")
        print(f"  📊 大小: {_path_size_mb(path):.1f}MB")
    else:
        print(f"  ❌ 未找到: {status['dictionary']}")

    return status["available"]

def check_config():
    """检查配置文件"""
    print("\n" + "=" * 60)
    print("⚙️  配置文件检查")
    print("=" * 60)

    config_ok = True

    # 检查 .env
    print("\n.env 文件:")
    if (PROJECT_ROOT / '.env').exists():
        with open(PROJECT_ROOT / '.env', 'r') as f:
            content = f.read()
            if 'mandarin_mfa' in content:
                print("  ✅ MFA 模型配置正确 (mandarin_mfa)")
            else:
                print("  ❌ MFA 模型配置错误")
                config_ok = False
    else:
        print("  ❌ .env 文件不存在")
        config_ok = False

    # 检查 config.py
    print("\nconfig.py 文件:")
    if (PROJECT_ROOT / 'config.py').exists():
        with open(PROJECT_ROOT / 'config.py', 'r') as f:
            content = f.read()
            if 'mandarin_mfa' in content:
                print("  ✅ MFA 模型配置正确 (mandarin_mfa)")
            if './models/CosyVoice2-0.5B' in content:
                print("  ✅ TTS 模型路径正确")
            else:
                print("  ⚠️  TTS 模型路径可能不正确")
    else:
        print("  ❌ config.py 文件不存在")
        config_ok = False

    return config_ok

def check_python_packages():
    """检查 Python 依赖"""
    print("\n" + "=" * 60)
    print("📚 Python 依赖检查")
    print("=" * 60)

    packages = [
        'torch',
        'fastapi',
        'uvicorn',
        'pydantic',
        'librosa',
    ]

    missing = []
    for pkg in packages:
        try:
            if importlib.util.find_spec(pkg) is None:
                raise ImportError(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg}")
            missing.append(pkg)

    return len(missing) == 0

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + "  🎵 TTS-Alignment-API 最终完整性检查".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    tts_ok = check_tts_models()
    mfa_ok = check_mfa_models()
    config_ok = check_config()
    python_ok = check_python_packages()

    print("\n" + "=" * 60)
    print("📊 检查结果总结")
    print("=" * 60)

    checks = [
        ("TTS 模型", tts_ok),
        ("MFA 中文模型", mfa_ok),
        ("配置文件", config_ok),
        ("Python 依赖", python_ok),
    ]

    for name, status in checks:
        status_str = "✅" if status else "❌"
        print(f"{status_str} {name}")

    all_ok = all(status for _, status in checks)

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ 一切就绪！可以启动 API 服务了")
        print("\n运行命令:")
        print("  uv sync")
        print("  bash scripts/run.sh")
        print("\n访问 API 文档:")
        print("  http://localhost:8000/docs")
        return 0
    else:
        print("❌ 有些问题需要解决")
        if not python_ok:
            print("\n安装 Python 依赖:")
            print("  uv sync")
        if not tts_ok:
            print("\n确保 TTS 模型在 ./models/ 目录下")
        if not mfa_ok:
            print("\nMFA 模型位置:")
            print(f"  声学模型: {settings.MFA_ACOUSTIC_MODEL}")
            print(f"  词典: {settings.MFA_DICTIONARY}")
            print("  详情: python3 scripts/check_mfa_ready.py")
        return 1

if __name__ == '__main__':
    sys.exit(main())
