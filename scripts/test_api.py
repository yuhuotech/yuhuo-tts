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
        self.project_root = Path(__file__).resolve().parent.parent
        self.sample_prompt = self.project_root / "third_party" / "CosyVoice" / "asset" / "zero_shot_prompt.wav"
        self.loaded_models = set()
        self.model_info = {}
        self.default_prompt_text = "希望你以后能够做的比我还好呦。"

    def _skip_if_model_unavailable(self, model_name: str) -> bool:
        if model_name in self.loaded_models:
            return False
        print(f"- 跳过 {model_name}: 当前服务未加载该模型")
        return True

    def _get_cosyvoice_request(self, text: str, output_format: str = "base64") -> dict:
        cosyvoice_info = self.model_info.get("cosyvoice2", {})
        speakers = cosyvoice_info.get("speakers") or []

        request = {
            "text": text,
            "model": "cosyvoice2",
            "output_format": output_format,
        }

        if speakers:
            request["mode"] = "sft"
            request["speaker"] = speakers[0]
            return request

        if not self.sample_prompt.exists():
            raise FileNotFoundError(f"未找到 CosyVoice zero-shot 参考音频: {self.sample_prompt}")

        request["mode"] = "zero_shot"
        request["prompt_audio"] = str(self.sample_prompt)
        request["prompt_text"] = self.default_prompt_text
        return request

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
            self.loaded_models = set(loaded_models)
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
            self.model_info = result["data"]
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
        if self._skip_if_model_unavailable("cosyvoice2"):
            return True
        try:
            test_text = "你好，这是一个测试。"

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json=self._get_cosyvoice_request(test_text, output_format="base64")
            )

            elapsed = time.time() - start_time
            result = response.json()

            assert result['status'] == 'success'
            assert 'alignments' in result['data']

            print(f"✓ CosyVoice2合成成功 ({elapsed:.2f}s)")
            print(f"  文本: {test_text}")
            print(f"  时长: {result['data']['duration']:.2f}s")
            print(f"  时间戳数: {len(result['data']['alignments'])}")

            # 打印前3个时间戳
            if result['data']['alignments']:
                print(f"  样本时间戳:")
                for ts in result['data']['alignments'][:3]:
                    print(f"    - {ts['char']}: {ts['start']:.3f}s - {ts['end']:.3f}s")
            else:
                print("  时间戳为空：当前配置或环境未输出 MFA 对齐结果")

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
        if self._skip_if_model_unavailable("qwen3"):
            return True
        try:
            test_text = "Hello, this is a test."
            if not self.sample_prompt.exists():
                raise FileNotFoundError(f"未找到测试参考音频: {self.sample_prompt}")

            upload_resp = self.session.post(
                f"{self.api_url}/upload_audio",
                files={"file": (self.sample_prompt.name, self.sample_prompt.read_bytes(), "audio/wav")}
            )
            upload_data = upload_resp.json()
            uploaded_audio_id = upload_data["data"]["uploaded_audio_id"]

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json={
                    "text": test_text,
                    "model": "qwen3",
                    "uploaded_audio_id": uploaded_audio_id,
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
        if self._skip_if_model_unavailable("cosyvoice2"):
            return True
        try:
            long_text = "今天天气真好，我们一起去公园玩吧。天空很蓝，阳光也很温暖。"

            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/synthesize",
                json=self._get_cosyvoice_request(long_text, output_format="base64")
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
            test_cases = []
            if "cosyvoice2" in self.loaded_models:
                test_cases.extend([
                    ("你好", "cosyvoice2"),
                    ("你好世界", "cosyvoice2"),
                    ("今天天气真好。", "cosyvoice2"),
                ])

            if "qwen3" in self.loaded_models and self.sample_prompt.exists():
                test_cases.append(("Hello", "qwen3"))

            if not test_cases:
                print("  - 跳过性能测试: 当前没有可测试模型")
                return True

            print("  文本 | 模型 | 时间")
            print("  ---|---|---")

            times = []
            for text, model in test_cases:
                start = time.time()
                response = self.session.post(
                    f"{self.api_url}/synthesize",
                    json=(
                        {
                            "text": text,
                            "model": model,
                            "output_format": "base64",
                            **(
                                {"uploaded_audio_id": self._upload_sample_prompt()}
                                if model == "qwen3"
                                else {}
                            )
                        }
                        if model == "qwen3"
                        else self._get_cosyvoice_request(text, output_format="base64")
                    )
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

    def _upload_sample_prompt(self) -> str:
        if not self.sample_prompt.exists():
            raise FileNotFoundError(f"未找到测试参考音频: {self.sample_prompt}")
        response = self.session.post(
            f"{self.api_url}/upload_audio",
            files={"file": (self.sample_prompt.name, self.sample_prompt.read_bytes(), "audio/wav")}
        )
        result = response.json()
        return result["data"]["uploaded_audio_id"]

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
