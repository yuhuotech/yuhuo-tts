"""性能基准测试"""

import time
import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings

def benchmark():
    """运行性能基准测试"""
    print("=" * 60)
    print("TTS-Alignment-API 性能基准测试")
    print("=" * 60)

    print("\n[提示] 此脚本用于本地性能测试")
    print("注意：实际的模型加载取决于已安装的模型库")

    # 模型加载性能
    print("\n[1] 模型加载性能...")
    start = time.time()
    try:
        from config import settings
        elapsed = time.time() - start
        print(f"✓ 配置加载: {elapsed:.3f}s")
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return

    # 测试工具函数
    print("\n[2] 工具函数性能...")
    from utils.audio_utils import normalize_audio, get_audio_duration

    # 生成测试音频
    test_audio = np.random.randn(44100)  # 1秒的音频

    # 规范化测试
    start = time.time()
    for _ in range(100):
        normalize_audio(test_audio)
    elapsed = time.time() - start
    print(f"✓ normalize_audio (100次): {elapsed:.3f}s")

    # 时长计算测试
    start = time.time()
    for _ in range(10000):
        get_audio_duration(test_audio, 44100)
    elapsed = time.time() - start
    print(f"✓ get_audio_duration (10000次): {elapsed:.3f}s")

    print("\n" + "=" * 60)
    print("基准测试完成")
    print("=" * 60)

if __name__ == "__main__":
    benchmark()
