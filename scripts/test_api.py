"""API测试脚本"""

import requests
import json
import base64
import time
from pathlib import Path

class APITester:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.session = requests.Session()

    def test_health(self) -> bool:
        """测试健康检查"""
        print("\n[Test 1] 健康检查...")
        try:
            response = self.session.get(f"{self.api_url}/health")
            result = response.json()

            assert response.status_code == 200
            assert result['status'] in ['ok', 'degraded']

            print(f"✓ 服务正常运行")
            loaded_models = [
                name for name, info in result['models'].items()
                if info['status'] == 'loaded'
            ]
            print(f"  已加载模型: {loaded_models}")
            print(f"  MFA状态: {result['mfa_enabled']}")
            return True
        except Exception as e:
            print(f"✗ 健康检查失败: {str(e)}")
            return False

    def test_models(self) -> bool:
        """测试模型列表"""
        print("\n[Test 2] 获取模型列表...")
        try:
            response = self.session.get(f"{self.api_url}/models")
            result = response.json()

            print(f"✓ 获取模型列表成功")
            for model_name, info in result['data'].items():
                print(f"  {model_name}:")
                print(f"    - 采样率: {info['sample_rate']}")
                print(f"    - 说话人: {info['speakers']}")
            return True
        except Exception as e:
            print(f"✗ 获取模型失败: {str(e)}")
            return False

    def test_synthesize_cosyvoice2(self) -> bool:
        """测试CosyVoice2合成"""
        print("\n[Test 3] CosyVoice2语音合成...")
        try:
            test_text = "你好，这是一个测试。"

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json={
                    "text": test_text,
                    "model": "cosyvoice2",
                    "mode": "sft",
                    "output_format": "base64"
                }
            )

            elapsed = time.time() - start_time
            result = response.json()

            assert result['status'] == 'success'
            assert 'alignments' in result['data']
            assert len(result['data']['alignments']) > 0

            print(f"✓ CosyVoice2合成成功 ({elapsed:.2f}s)")
            print(f"  文本: {test_text}")
            print(f"  时长: {result['data']['duration']:.2f}s")
            print(f"  时间戳数: {len(result['data']['alignments'])}")

            # 打印前3个时间戳
            print(f"  样本时间戳:")
            for ts in result['data']['alignments'][:3]:
                print(f"    - {ts['char']}: {ts['start']:.3f}s - {ts['end']:.3f}s")

            # 保存音频
            if 'audio' in result['data']:
                audio_bytes = base64.b64decode(result['data']['audio'])
                with open('test_cosyvoice2.wav', 'wb') as f:
                    f.write(audio_bytes)
                print(f"  音频已保存: test_cosyvoice2.wav")

            return True
        except Exception as e:
            print(f"✗ CosyVoice2合成失败: {str(e)}")
            return False

    def test_synthesize_qwen3(self) -> bool:
        """测试Qwen3-TTS合成"""
        print("\n[Test 4] Qwen3-TTS语音合成...")
        try:
            test_text = "Hello, this is a test."

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json={
                    "text": test_text,
                    "model": "qwen3",
                    "output_format": "url"
                }
            )

            elapsed = time.time() - start_time
            result = response.json()

            assert result['status'] == 'success'
            assert 'alignments' in result['data']

            print(f"✓ Qwen3-TTS合成成功 ({elapsed:.2f}s)")
            print(f"  文本: {test_text}")
            print(f"  时长: {result['data']['duration']:.2f}s")
            print(f"  文件URL: {result['data'].get('audio_url', 'N/A')}")

            return True
        except Exception as e:
            print(f"✗ Qwen3-TTS合成失败: {str(e)}")
            return False

    def test_long_text(self) -> bool:
        """测试长文本合成"""
        print("\n[Test 5] 长文本合成...")
        try:
            long_text = "今天天气真好，我们一起去公园玩吧。天空很蓝，阳光也很温暖。"

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json={
                    "text": long_text,
                    "model": "cosyvoice2",
                    "output_format": "base64"
                }
            )

            elapsed = time.time() - start_time
            result = response.json()

            assert result['status'] == 'success'

            print(f"✓ 长文本合成成功 ({elapsed:.2f}s)")
            print(f"  文本长度: {len(long_text)}字")
            print(f"  音频时长: {result['data']['duration']:.2f}s")
            print(f"  时间戳数: {len(result['data']['alignments'])}")

            return True
        except Exception as e:
            print(f"✗ 长文本合成失败: {str(e)}")
            return False

    def test_performance(self) -> bool:
        """性能测试"""
        print("\n[Test 6] 性能测试...")
        try:
            test_cases = [
                ("你好", "cosyvoice2"),
                ("你好世界", "cosyvoice2"),
                ("今天天气真好。", "cosyvoice2"),
                ("Hello", "qwen3"),
            ]

            print("  文本 | 模型 | 时间")
            print("  ---|---|---")

            times = []
            for text, model in test_cases:
                start = time.time()
                response = self.session.post(
                    f"{self.api_url}/synthesize",
                    json={"text": text, "model": model, "output_format": "base64"}
                )
                elapsed = time.time() - start
                times.append(elapsed)

                print(f"  {text} | {model} | {elapsed:.2f}s")

            avg_time = sum(times) / len(times)
            print(f"\n✓ 性能测试完成 (平均: {avg_time:.2f}s)")
            return True
        except Exception as e:
            print(f"✗ 性能测试失败: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("TTS-Alignment-API 测试套件")
        print("=" * 50)

        tests = [
            self.test_health,
            self.test_models,
            self.test_synthesize_cosyvoice2,
            self.test_synthesize_qwen3,
            self.test_long_text,
            self.test_performance,
        ]

        results = []
        for test in tests:
            try:
                result = test()
                results.append((test.__name__, result))
            except Exception as e:
                print(f"✗ 测试异常: {str(e)}")
                results.append((test.__name__, False))

        print("\n" + "=" * 50)
        print("测试总结")
        print("=" * 50)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{status}: {test_name}")

        print(f"\n总计: {passed}/{total} 通过")

        return passed == total

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
