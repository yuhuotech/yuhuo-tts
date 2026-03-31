#!/usr/bin/env python3
"""
测试 MFA 中文模型是否正确处理中文时间戳
"""

import os
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from alignment.mfa_aligner import MFAAligner

def test_mfa_models_exist():
    """检查 MFA 模型是否已下载"""
    print("=" * 60)
    print("🔍 检查 MFA 模型文件")
    print("=" * 60)

    acoustic_candidates = [
        Path.home() / '.mfa' / 'models' / 'acoustic_models' / settings.MFA_ACOUSTIC_MODEL,
        Path.home() / 'Documents' / 'MFA' / 'pretrained_models' / 'acoustic' / f'{settings.MFA_ACOUSTIC_MODEL}.zip',
    ]
    dict_candidates = [
        Path.home() / '.mfa' / 'models' / 'dictionary_models' / f'{settings.MFA_DICTIONARY}.dict',
        Path.home() / '.mfa' / 'models' / 'g2p_models' / settings.MFA_DICTIONARY,
        Path.home() / 'Documents' / 'MFA' / 'pretrained_models' / 'dictionary' / f'{settings.MFA_DICTIONARY}.dict',
    ]

    acoustic_dir = next((p for p in acoustic_candidates if p.exists()), acoustic_candidates[0])
    dict_dir = next((p for p in dict_candidates if p.exists()), dict_candidates[0])

    acoustic_ok = acoustic_dir.exists()
    dict_ok = dict_dir.exists()

    if acoustic_ok:
        if acoustic_dir.is_file():
            files = [acoustic_dir]
            size = acoustic_dir.stat().st_size / (1024**2)
        else:
            files = list(acoustic_dir.glob('*'))
            size = sum(f.stat().st_size for f in files if f.is_file()) / (1024**2)
        print(f"✅ 声学模型（Acoustic Model）")
        print(f"   位置: {acoustic_dir}")
        print(f"   文件数: {len(files)}, 大小: {size:.1f}MB\n")
    else:
        print(f"❌ 声学模型未找到: {acoustic_dir}\n")

    if dict_ok:
        if dict_dir.is_file():
            files = [dict_dir]
            size = dict_dir.stat().st_size / (1024**2)
        else:
            files = list(dict_dir.glob('*'))
            size = sum(f.stat().st_size for f in files if f.is_file()) / (1024**2)
        print(f"✅ 发音词典（Dictionary）")
        print(f"   位置: {dict_dir}")
        print(f"   文件数: {len(files)}, 大小: {size:.1f}MB\n")
    else:
        print(f"❌ 词典未找到: {dict_dir}\n")

    return acoustic_ok and dict_ok

def generate_test_audio():
    """生成降级用测试音频（仅在真实语音样本缺失时使用）"""
    print("=" * 60)
    print("🔊 生成测试音频")
    print("=" * 60)

    sample_rate = 16000
    duration = 2  # 2 秒

    # 生成简单的正弦波音频
    t = np.linspace(0, duration, int(sample_rate * duration))
    # 使用多个频率模拟语音
    frequency1 = 400  # 较低频率
    frequency2 = 2000  # 较高频率
    audio = 0.3 * np.sin(2 * np.pi * frequency1 * t) + 0.2 * np.sin(2 * np.pi * frequency2 * t)

    # 添加包络（渐进式增长和衰减）
    envelope = np.concatenate([
        np.linspace(0, 1, int(sample_rate * 0.2)),  # 上升
        np.ones(int(sample_rate * 1.6)),             # 平稳
        np.linspace(1, 0, int(sample_rate * 0.2))   # 下降
    ])
    audio = audio * envelope

    print(f"✅ 测试音频生成成功")
    print(f"   采样率: {sample_rate} Hz")
    print(f"   时长: {duration} 秒")
    print(f"   峰值: {np.max(np.abs(audio)):.3f}\n")

    return audio, sample_rate

def load_reference_audio():
    """优先加载真实中文语音样本。"""
    sample_path = PROJECT_ROOT / "third_party" / "CosyVoice" / "asset" / "zero_shot_prompt.wav"
    sample_text = "希望你以后能够做的比我还好呦。"

    if sample_path.exists():
        print("=" * 60)
        print("🎤 加载真实中文语音样本")
        print("=" * 60)
        audio, sample_rate = sf.read(sample_path)
        print(f"✅ 样本已加载")
        print(f"   路径: {sample_path}")
        print(f"   采样率: {sample_rate} Hz")
        print(f"   时长: {len(audio) / sample_rate:.2f} 秒")
        print(f"   文本: {sample_text}\n")
        return audio, sample_rate, sample_text

    print("⚠️  未找到真实语音样本，退回合成正弦波测试\n")
    audio, sample_rate = generate_test_audio()
    return audio, sample_rate, "你好世界"

def test_mfa_alignment(audio, sample_rate, text="你好世界"):
    """测试 MFA 中文对齐"""
    print("=" * 60)
    print("🎯 测试 MFA 中文对齐")
    print("=" * 60)
    print(f"输入文本: '{text}'")
    print(f"文本长度: {len(text)} 个字符\n")

    try:
        print("⏳ 运行 MFAAligner.align()...")
        start_time = time.time()
        alignments = MFAAligner().align(audio, text, sample_rate)
        elapsed = time.time() - start_time

        print(f"⏱️  耗时: {elapsed:.1f} 秒")

        if not alignments:
            print("❌ 未返回时间戳\n")
            return False, None

        print("✅ MFA 对齐成功！\n")
        print("✅ 对齐结果（按时间顺序）：\n")
        print(f"{'字符':<6} {'开始时间':<12} {'结束时间':<12} {'置信度':<8}")
        print("-" * 40)
        for item in alignments[:12]:
            print(f"{item['char']:<6} {item['start']:<12.3f} {item['end']:<12.3f} {item['confidence']:<8.2f}")
        if len(alignments) > 12:
            print(f"... 共 {len(alignments)} 条")
        print()

        total_duration = len(audio) / sample_rate
        max_end = max(item['end'] for item in alignments)

        if max_end <= total_duration * 1.1:
            print(f"✅ 时间戳合理")
            print(f"   音频时长: {total_duration:.3f} 秒")
            print(f"   对齐最后位置: {max_end:.3f} 秒\n")
            return True, alignments

        print(f"⚠️  时间戳异常")
        print(f"   音频时长: {total_duration:.3f} 秒")
        print(f"   对齐最后位置: {max_end:.3f} 秒\n")
        return False, alignments
    except Exception as e:
        print(f"❌ 出现异常: {e}\n")
        return False, None

def parse_textgrid(textgrid_path):
    """解析 TextGrid 文件"""
    try:
        import re

        with open(textgrid_path, 'r', encoding='utf-8') as f:
            content = f.read()

        alignments = []

        # 提取所有 intervals
        pattern = r'intervals \[(\d+)\]:\s*xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)?"'
        matches = re.findall(pattern, content)

        for idx, xmin, xmax, text in matches:
            if text and text.strip() and text not in ['<sil>', '<silence>']:
                alignments.append({
                    'char': text,
                    'start': float(xmin),
                    'end': float(xmax),
                    'confidence': 0.90
                })

        return alignments
    except Exception as e:
        print(f"解析 TextGrid 异常: {e}")
        return None

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🎵 MFA 中文模型完整性测试".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    aligner = MFAAligner()
    status = aligner.get_status(force_refresh=True)
    print("MFA 状态:")
    print(f"  available: {status['available']}")
    print(f"  reason: {status['reason']}")
    print(f"  command_path: {status['command_path']}")
    print(f"  command_error: {status['command_error']}")
    print(f"  acoustic_model_path: {status['acoustic_model_path']}")
    print(f"  dictionary_path: {status['dictionary_path']}")
    print()

    # 1. 检查模型文件
    models_ok = test_mfa_models_exist()

    if not models_ok:
        print("⏳ MFA 模型还在下载中...")
        print("   请稍等几分钟后重新运行此脚本")
        print("   或检查: ~/.mfa/models/")
        return 1

    # 2. 加载真实样本，缺失时退回合成音
    audio, sample_rate, sample_text = load_reference_audio()

    # 3. 测试 MFA 对齐
    success, alignments = test_mfa_alignment(audio, sample_rate, text=sample_text)

    if not success:
        print("⚠️  MFA 对齐测试失败")
        print("   降级方案仍然可用（时间戳会均匀分布）")
        return 1

    # 4. 总结
    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    print("\n🎉 MFA 中文模型已准备就绪！")
    print("   - 声学模型: ✅")
    print("   - 词典: ✅")
    print("   - 中文对齐: ✅")
    print("\n现在可以启动 API 服务，使用精确的字级时间戳对齐功能。\n")

    return 0

if __name__ == '__main__':
    sys.exit(main())
