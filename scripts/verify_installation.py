#!/usr/bin/env python3
"""
验证 TTS-Alignment-API 安装完整性
"""

import os
import sys
from pathlib import Path
import json
import importlib.util

if str(PROJECT_ROOT := Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from alignment.mfa_aligner import MFAAligner

def check_models():
    """检查模型文件完整性"""
    print("\n📦 检查模型文件...")
    models_dir = PROJECT_ROOT / "models"
    results = {}

    # 检查 CosyVoice2
    cosyvoice2_dir = models_dir / "CosyVoice2-0.5B"
    cosyvoice2_files = [
        "llm.pt",
        "flow.pt",
        "hift.pt",
        "speech_tokenizer_v2.onnx",
        "flow.decoder.estimator.fp32.onnx",
        "campplus.onnx",
        "config.json",
        "cosyvoice2.yaml",
        "CosyVoice-BlankEN/model.safetensors"
    ]

    cosyvoice2_ok = all((cosyvoice2_dir / f).exists() for f in cosyvoice2_files)
    results['CosyVoice2'] = {
        'status': '✅' if cosyvoice2_ok else '❌',
        'path': str(cosyvoice2_dir.relative_to(PROJECT_ROOT)),
        'missing': [f for f in cosyvoice2_files if not (cosyvoice2_dir / f).exists()]
    }
    print(f"  CosyVoice2: {results['CosyVoice2']['status']}")
    if results['CosyVoice2']['missing']:
        print(f"    缺失: {results['CosyVoice2']['missing']}")

    # 检查 Qwen3-TTS
    qwen3_dir = models_dir / "Qwen3-TTS-12Hz-1.7B-Base"
    qwen3_files = [
        "config.json",
        "tokenizer_config.json",
        "generation_config.json",
        "vocab.json",
        "merges.txt",
        "speech_tokenizer/model.safetensors"
    ]

    qwen3_ok = all((qwen3_dir / f).exists() for f in qwen3_files)
    results['Qwen3-TTS'] = {
        'status': '✅' if qwen3_ok else '❌',
        'path': str(qwen3_dir.relative_to(PROJECT_ROOT)),
        'missing': [f for f in qwen3_files if not (qwen3_dir / f).exists()]
    }
    print(f"  Qwen3-TTS: {results['Qwen3-TTS']['status']}")
    if results['Qwen3-TTS']['missing']:
        print(f"    缺失: {results['Qwen3-TTS']['missing']}")

    # 模型大小
    if cosyvoice2_dir.exists():
        size_gb = sum(f.stat().st_size for f in cosyvoice2_dir.rglob('*') if f.is_file()) / (1024**3)
        print(f"    大小: {size_gb:.1f}GB")

    if qwen3_dir.exists():
        size_gb = sum(f.stat().st_size for f in qwen3_dir.rglob('*') if f.is_file()) / (1024**3)
        print(f"    大小: {size_gb:.1f}GB")

    return results

def check_dependencies():
    """检查 Python 依赖"""
    print("\n📚 检查 Python 依赖...")
    dependencies = [
        'fastapi', 'uvicorn', 'pydantic', 'torch', 'torchaudio',
        'librosa', 'soundfile', 'numpy', 'scipy', 'yaml',
        'textgrid', 'qwen_tts'
    ]

    missing = []
    for dep in dependencies:
        if importlib.util.find_spec(dep) is not None:
            print(f"  ✅ {dep}")
        else:
            print(f"  ❌ {dep}")
            missing.append(dep)

    return missing

def check_directories():
    """检查必要目录"""
    print("\n📁 检查目录结构...")
    dirs = [
        'models', 'alignment', 'utils',
        'temp_audio', 'output_audio', 'logs'
    ]

    results = {}
    for d in dirs:
        path = Path(d)
        exists = (PROJECT_ROOT / path).exists()
        results[d] = exists
        print(f"  {'✅' if exists else '❌'} {d}")

    return results

def check_mfa():
    """检查 MFA 安装"""
    print("\n🔤 检查 MFA...")
    status = MFAAligner().get_status(force_refresh=True)
    print(f"  enabled: {status['enabled']}")
    print(f"  available: {status['available']}")
    print(f"  command_available: {status['command_available']}")
    print(f"  command_path: {status['command_path']}")
    print(f"  command_error: {status['command_error']}")
    print(f"  声学模型配置: {status['acoustic_model']}")
    print(f"  声学模型路径: {status['acoustic_model_path']}")
    print(f"  词典配置: {status['dictionary']}")
    print(f"  词典路径: {status['dictionary_path']}")
    print(f"  fallback_alignment: {status['fallback_alignment']}")
    print(f"  reason: {status['reason']}")
    return status["available"]

def check_config():
    """检查配置文件"""
    print("\n⚙️  检查配置文件...")
    config_files = ['.env', 'config.py', 'requirements.txt']

    for f in config_files:
        exists = (PROJECT_ROOT / f).exists()
        print(f"  {'✅' if exists else '❌'} {f}")

def main():
    print("=" * 50)
    print("🔍 TTS-Alignment-API 安装完整性检查")
    print("=" * 50)

    models_ok = check_models()
    deps_missing = check_dependencies()
    dirs_ok = check_directories()
    mfa_ok = check_mfa()
    check_config()

    print("\n" + "=" * 50)
    print("📊 检查总结")
    print("=" * 50)

    all_ok = (
        all(m['status'] == '✅' for m in models_ok.values()) and
        not deps_missing and
        all(dirs_ok.values()) and
        mfa_ok
    )

    if all_ok:
        print("✅ 一切就绪！可以启动 API 服务了")
        print("\n启动命令:")
        print("  bash scripts/run.sh")
        return 0
    else:
        print("⚠️  有些问题需要处理:")
        if any(m['status'] == '❌' for m in models_ok.values()):
            print("  - 模型文件不完整，请继续等待下载")
        if deps_missing:
            print(f"  - 缺失依赖: {', '.join(deps_missing)}")
            print("    运行: uv sync")
        if not mfa_ok:
            print("  - MFA 安装或模型有问题")
            print("    运行: python3 scripts/check_mfa_ready.py")
        if not all(dirs_ok.values()):
            print("  - 缺少必要目录")
        return 1

if __name__ == '__main__':
    sys.exit(main())
