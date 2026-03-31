#!/usr/bin/env python3
"""
CosyVoice 环境检查脚本
验证所有必要的依赖和配置是否正确
"""

import sys
import os
import importlib.util

# 自动设置 PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matcha_path = os.path.join(project_root, 'third_party/CosyVoice/third_party/Matcha-TTS')
if os.path.exists(matcha_path):
    sys.path.insert(0, matcha_path)
    print(f"✓ Matcha-TTS 路径已添加到 sys.path")
else:
    print(f"✗ Matcha-TTS 路径不存在: {matcha_path}")

cosyvoice_root = os.path.join(project_root, 'third_party/CosyVoice')
if os.path.exists(cosyvoice_root):
    sys.path.insert(0, cosyvoice_root)
    print(f"✓ CosyVoice 路径已添加到 sys.path")
else:
    print(f"✗ CosyVoice 路径不存在: {cosyvoice_root}")

print("\n" + "="*60)
print("CosyVoice 环境检查")
print("="*60 + "\n")

# 检查 Python 版本
print(f"Python 版本: {sys.version}")
if sys.version_info >= (3, 11):
    print("⚠️  警告: Python 3.11+ 可能存在兼容性问题（官方建议 3.8-3.10）")

# 检查必要的包
checks = [
    ("torch", "PyTorch"),
    ("numpy", "NumPy"),
    ("scipy", "SciPy"),
    ("librosa", "librosa"),
    ("soundfile", "soundfile"),
    ("torchaudio", "torchaudio"),
    ("pynini", "pynini"),
]

print("\n检查依赖包：")
print("-" * 60)
all_installed = True
for module_name, display_name in checks:
    if importlib.util.find_spec(module_name) is not None:
        print(f"✓ {display_name:<20} 已安装")
    else:
        print(f"✗ {display_name:<20} 未安装")
        all_installed = False

# 检查 CosyVoice
print("\n检查 CosyVoice 模块：")
print("-" * 60)
try:
    from cosyvoice.cli.cosyvoice import AutoModel
    print("✓ CosyVoice 导入成功")
except ImportError as e:
    print(f"✗ CosyVoice 导入失败: {e}")
    all_installed = False

# 检查模型文件
print("\n检查模型文件：")
print("-" * 60)
model_paths = {
    "CosyVoice2": "models/CosyVoice2-0.5B/cosyvoice2.yaml",
    "Qwen3-TTS": "models/Qwen3-TTS-12Hz-1.7B-Base/model.safetensors",
}

for model_name, model_file in model_paths.items():
    full_path = os.path.join(project_root, model_file)
    if os.path.exists(full_path):
        print(f"✓ {model_name:<20} {full_path}")
    else:
        print(f"✗ {model_name:<20} 未找到: {model_file}")

# 尝试加载 CosyVoice 模型
print("\n检查模型加载：")
print("-" * 60)
try:
    model_dir = os.path.join(project_root, "models/CosyVoice2-0.5B")
    if os.path.exists(model_dir):
        from cosyvoice.cli.cosyvoice import AutoModel
        print("正在加载 CosyVoice2 模型（这可能需要一些时间）...")
        model = AutoModel(model_dir=model_dir)
        print("✓ CosyVoice2 模型加载成功")

        # 获取可用音色
        try:
            speakers = model.list_available_spks()
            print(f"✓ 可用音色: {speakers}")
        except:
            print("⚠️  无法获取音色列表")
    else:
        print(f"⚠️  模型未下载: {model_dir}")
        print("   请运行: bash scripts/install.sh")
except Exception as e:
    print(f"✗ 模型加载失败: {e}")

# 总结
print("\n" + "="*60)
if all_installed and os.path.exists(os.path.join(project_root, "models/CosyVoice2-0.5B")):
    print("✓ 环境检查通过！可以启动应用")
    print("\n启动命令:")
    print("  uv sync")
    print("  bash scripts/run.sh")
else:
    print("✗ 环境检查未完全通过")
    print("\n请执行以下步骤:")
    print("  1. bash scripts/install.sh          # 安装依赖和下载模型")
    print("  2. uv run python scripts/test_cosyvoice.py")
    print("  3. bash scripts/run.sh")
print("="*60)
