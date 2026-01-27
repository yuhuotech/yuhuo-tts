#!/usr/bin/env python3
"""
最终完整性检查 - 确保所有模型和配置都就绪
"""

import os
import sys
from pathlib import Path

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

    base_path = Path('./models')
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

    mfa_path = Path.home() / 'Documents' / 'MFA' / 'pretrained_models'
    models_ok = True

    # 检查声学模型
    acoustic_path = mfa_path / 'acoustic' / 'mandarin_mfa.zip'
    print(f"\n声学模型 (mandarin_mfa):")
    if acoustic_path.exists():
        size_mb = acoustic_path.stat().st_size / (1024**2)
        print(f"  ✅ {acoustic_path}")
        print(f"  📊 大小: {size_mb:.1f}MB")
    else:
        print(f"  ❌ 不存在: {acoustic_path}")
        models_ok = False

    # 检查词典
    dict_path = mfa_path / 'dictionary' / 'mandarin_mfa.dict'
    print(f"\n词典 (mandarin_mfa):")
    if dict_path.exists():
        size_mb = dict_path.stat().st_size / (1024**2)
        print(f"  ✅ {dict_path}")
        print(f"  📊 大小: {size_mb:.1f}MB")
    else:
        print(f"  ❌ 不存在: {dict_path}")
        models_ok = False

    return models_ok

def check_config():
    """检查配置文件"""
    print("\n" + "=" * 60)
    print("⚙️  配置文件检查")
    print("=" * 60)

    config_ok = True

    # 检查 .env
    print("\n.env 文件:")
    if Path('.env').exists():
        with open('.env', 'r') as f:
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
    if Path('config.py').exists():
        with open('config.py', 'r') as f:
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
            __import__(pkg)
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
        print("  python app.py")
        print("\n访问 API 文档:")
        print("  http://localhost:8000/docs")
        return 0
    else:
        print("❌ 有些问题需要解决")
        if not python_ok:
            print("\n安装 Python 依赖:")
            print("  pip install -r requirements.txt")
        if not tts_ok:
            print("\n确保 TTS 模型在 ./models/ 目录下")
        if not mfa_ok:
            print("\nMFA 模型位置:")
            print("  声学模型: ~/Documents/MFA/pretrained_models/acoustic/mandarin_mfa.zip")
            print("  词典: ~/Documents/MFA/pretrained_models/dictionary/mandarin_mfa.dict")
        return 1

if __name__ == '__main__':
    sys.exit(main())
