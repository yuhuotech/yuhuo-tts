"""Montreal Forced Aligner - 字级对齐"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import soundfile as sf
from config import settings

class MFAAligner:
    """Montreal Forced Aligner - 字级对齐"""

    def __init__(self):
        self.acoustic_model = settings.MFA_ACOUSTIC_MODEL
        self.dictionary = settings.MFA_DICTIONARY
        self.command = settings.MFA_COMMAND.strip()
        self.temp_dir = settings.TEMP_AUDIO_DIR
        self.enabled = settings.MFA_ENABLE
        self.fallback_alignment = settings.MFA_FALLBACK_ALIGNMENT
        self._status_cache: Optional[Dict] = None
        self._command_error: Optional[str] = None
        self._resolved_command: Optional[str] = None

    def align(
        self,
        audio: np.ndarray,
        text: str,
        sample_rate: int
    ) -> List[Dict]:
        """
        对齐文本和音频

        Args:
            audio: 音频波形
            text: 文本
            sample_rate: 采样率

        Returns:
            [{"char": "你", "start": 0.0, "end": 0.45, "confidence": 0.92}, ...]
        """
        duration = len(audio) / sample_rate
        prepared_text = self._prepare_text(text)

        if not self.enabled:
            return self._handle_fallback(
                text=text,
                duration=duration,
                reason="MFA 已禁用"
            )

        if not prepared_text["normalized_text"]:
            print("⚠️  MFA 规范化后无可对齐文本，不输出时间戳")
            return []

        mfa_status = self.get_status(force_refresh=True)
        if not mfa_status["available"]:
            return self._handle_fallback(
                text=text,
                duration=duration,
                reason=f"MFA 不可用: {mfa_status['reason']}"
            )

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # 保存音频和文本
                audio_path = os.path.join(tmpdir, "audio.wav")
                text_path = os.path.join(tmpdir, "audio.lab")
                output_dir = os.path.join(tmpdir, "output")

                sf.write(audio_path, audio, sample_rate)

                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(prepared_text["normalized_text"])

                # 运行MFA
                mfa_command = self._resolve_mfa_command()
                if mfa_command is None:
                    return self._handle_fallback(
                        text=text,
                        duration=duration,
                        reason="MFA 命令未找到"
                    )

                result = subprocess.run([
                    mfa_command, "align",
                    tmpdir,
                    self.dictionary,
                    self.acoustic_model,
                    output_dir,
                    "--overwrite",
                    "--single_speaker"
                ], capture_output=True, text=True, timeout=settings.MFA_TIMEOUT)

                if result.returncode != 0:
                    return self._handle_fallback(
                        text=text,
                        duration=duration,
                        reason=f"MFA对齐失败: {result.stderr[:200]}"
                    )

                # 解析TextGrid
                alignments = self._parse_textgrid(
                    os.path.join(output_dir, "audio.TextGrid"),
                    prepared_text["token_groups"]
                )

                if alignments:
                    print(f"✅ MFA对齐成功: {len(alignments)} 个字符")
                    return alignments
                else:
                    return self._handle_fallback(
                        text=text,
                        duration=duration,
                        reason="TextGrid 解析后无有效时间戳"
                    )

        except FileNotFoundError:
            return self._handle_fallback(
                text=text,
                duration=duration,
                reason="MFA 命令未找到"
            )
        except subprocess.TimeoutExpired:
            return self._handle_fallback(
                text=text,
                duration=duration,
                reason=f"MFA 对齐超时 (>{settings.MFA_TIMEOUT}s)"
            )
        except Exception as e:
            return self._handle_fallback(
                text=text,
                duration=duration,
                reason=f"MFA对齐异常: {str(e)}"
            )

    def _parse_textgrid(self, textgrid_path: str, token_groups: Optional[List[Dict]] = None) -> List[Dict]:
        """解析TextGrid文件"""
        try:
            from textgrid import TextGrid
        except ImportError:
            print("警告: textgrid库未安装，使用降级方案")
            return []

        try:
            tg = TextGrid.fromFile(textgrid_path)
            tier = self._select_alignment_tier(tg)
            if tier is None:
                return []

            intervals = [
                interval for interval in tier.intervals
                if interval.mark.strip() and interval.mark.strip() not in ['<sil>', '<silence>', 'sp', 'sil']
            ]
            if not intervals:
                return []

            if token_groups:
                return self._build_alignments_from_token_groups(intervals, token_groups)

            alignments = []
            for interval in intervals:
                alignments.extend(
                    self._expand_interval_to_chars(
                        interval.mark.strip(),
                        interval.minTime,
                        interval.maxTime,
                    )
                )
            return alignments

        except Exception as e:
            print(f"TextGrid解析失败: {str(e)}")
            return []

    def _select_alignment_tier(self, textgrid) -> Optional[object]:
        preferred_patterns = ("word", "words", "token", "tokens")

        for pattern in preferred_patterns:
            for tier in textgrid.tiers:
                if pattern in tier.name.lower():
                    return tier

        for tier in textgrid.tiers:
            if getattr(tier, "intervals", None):
                return tier
        return None

    def _build_alignments_from_token_groups(self, intervals: List[object], token_groups: List[Dict]) -> List[Dict]:
        alignments = []
        group_index = 0

        for interval in intervals:
            mark = interval.mark.strip()
            group = self._match_interval_to_group(mark, token_groups, group_index)
            if group is None:
                alignments.extend(
                    self._expand_interval_to_chars(
                        mark,
                        interval.minTime,
                        interval.maxTime,
                    )
                )
                continue

            group_index = group["index"] + 1
            alignments.extend(
                self._expand_interval_to_chars(
                    mark,
                    interval.minTime,
                    interval.maxTime,
                    group["chars"]
                )
            )

        return alignments

    def _match_interval_to_group(self, mark: str, token_groups: List[Dict], start_index: int) -> Optional[Dict]:
        normalized_mark = self._normalize_token(mark)

        for index in range(start_index, len(token_groups)):
            group = token_groups[index]
            if group["normalized"] == normalized_mark:
                return {"index": index, "chars": group["chars"]}

        if start_index < len(token_groups):
            return {"index": start_index, "chars": token_groups[start_index]["chars"]}
        return None

    def _expand_interval_to_chars(
        self,
        mark: str,
        start_time: float,
        end_time: float,
        original_chars: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        将 MFA 的词级区间尽量展开为字级结果。

        对中文连续字符，按区间均分为单字时间戳；
        对非中文或包含空格的片段，保留原片段。
        """
        if re.search(r"[\u4e00-\u9fffA-Za-z0-9]", mark) and " " not in mark and len(mark) > 1:
            chars = list(mark)
            if original_chars and len(original_chars) >= len(chars):
                chars = original_chars[:len(chars)]
            char_duration = (end_time - start_time) / len(chars)
            return [
                {
                    "char": char,
                    "start": round(start_time + idx * char_duration, 3),
                    "end": round(start_time + (idx + 1) * char_duration, 3),
                    "confidence": 0.84,
                }
                for idx, char in enumerate(chars)
            ]

        if original_chars:
            mark = original_chars[0]

        return [{
            "char": mark,
            "start": round(start_time, 3),
            "end": round(end_time, 3),
            "confidence": 0.88
        }]

    def _check_mfa_available(self) -> bool:
        """检查MFA是否可用"""
        command = self._resolve_mfa_command()
        if command is None:
            return False
        return True

    def get_status(self, force_refresh: bool = False) -> Dict:
        if force_refresh:
            self._status_cache = None
            self._resolved_command = None
            self._command_error = None

        if self._status_cache is not None and not force_refresh:
            return self._status_cache

        command_available = self._check_mfa_available()
        command_path = self._resolve_mfa_command()
        acoustic_path = self._resolve_acoustic_model_path()
        dictionary_path = self._resolve_dictionary_path()
        acoustic_available = acoustic_path is not None
        dictionary_available = dictionary_path is not None

        reason_parts = []
        if not self.enabled:
            reason_parts.append("MFA disabled")
        if not command_available:
            if command_path:
                reason_parts.append("mfa command unusable")
            else:
                reason_parts.append("mfa command missing")
        if not acoustic_available:
            reason_parts.append(f"acoustic model missing: {self.acoustic_model}")
        if not dictionary_available:
            reason_parts.append(f"dictionary missing: {self.dictionary}")
        if self._command_error:
            reason_parts.append(self._command_error)

        self._status_cache = {
            "enabled": self.enabled,
            "available": self.enabled and command_available and acoustic_available and dictionary_available,
            "command_available": command_available,
            "command_path": command_path,
            "command_error": self._command_error,
            "acoustic_model": self.acoustic_model,
            "dictionary": self.dictionary,
            "acoustic_model_path": str(acoustic_path) if acoustic_path else None,
            "dictionary_path": str(dictionary_path) if dictionary_path else None,
            "fallback_alignment": self.fallback_alignment,
            "reason": ", ".join(reason_parts) if reason_parts else "ready",
        }
        return self._status_cache

    def _resolve_mfa_command(self) -> Optional[str]:
        if self._resolved_command is not None:
            return self._resolved_command

        candidates: List[str] = []

        if self.command:
            candidates.append(self.command)

        path_command = shutil.which("mfa")
        if path_command:
            candidates.append(path_command)

        for path_entry in os.environ.get("PATH", "").split(os.pathsep):
            if not path_entry:
                continue
            candidates.append(str(Path(path_entry) / "mfa"))

        interpreter_dir = Path(sys.executable).resolve().parent
        candidates.extend([
            str(interpreter_dir / "mfa"),
            str(Path.cwd() / ".venv" / "bin" / "mfa"),
            str(Path(__file__).resolve().parent.parent / ".venv" / "bin" / "mfa"),
        ])

        seen = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)

            candidate_path = Path(candidate)
            if candidate_path.is_file() and os.access(candidate_path, os.X_OK):
                candidate = str(candidate_path)
            else:
                resolved = shutil.which(candidate)
                if not resolved:
                    continue
                candidate = resolved

            error_text = self._probe_mfa_command(candidate)
            if error_text is None:
                self._resolved_command = str(candidate)
                self._command_error = None
                return self._resolved_command
            self._command_error = error_text

        self._resolved_command = None
        return None

    def _probe_mfa_command(self, command: str) -> Optional[str]:
        try:
            result = subprocess.run(
                [command, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return None

            error_text = (result.stderr or result.stdout or "").strip()
            return error_text[:300] if error_text else "mfa exited with non-zero status"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return "mfa executable not runnable"

    def _resolve_acoustic_model_path(self) -> Optional[Path]:
        candidates = [
            Path.home() / ".mfa" / "models" / "acoustic_models" / self.acoustic_model,
            Path.home() / "Documents" / "MFA" / "pretrained_models" / "acoustic" / f"{self.acoustic_model}.zip",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _resolve_dictionary_path(self) -> Optional[Path]:
        candidates = [
            Path.home() / ".mfa" / "models" / "dictionary_models" / f"{self.dictionary}.dict",
            Path.home() / ".mfa" / "models" / "g2p_models" / self.dictionary,
            Path.home() / "Documents" / "MFA" / "pretrained_models" / "dictionary" / f"{self.dictionary}.dict",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _prepare_text(self, text: str) -> Dict:
        normalized_text_parts = []
        char_map = []
        token_groups: List[Dict] = []
        current_token_chars: List[str] = []
        current_token_normalized: List[str] = []
        previous_was_space = True

        for original_char in text:
            normalized_char = unicodedata.normalize("NFKC", original_char)
            if normalized_char.isspace():
                self._flush_current_token(token_groups, current_token_chars, current_token_normalized)
                if not previous_was_space:
                    normalized_text_parts.append(" ")
                    previous_was_space = True
                continue

            if self._is_alignable_char(normalized_char):
                normalized_token_char = self._normalize_token(normalized_char)
                normalized_text_parts.append(normalized_token_char)
                char_map.append(original_char)
                current_token_chars.append(original_char)
                current_token_normalized.append(normalized_token_char)
                previous_was_space = False
                continue

            self._flush_current_token(token_groups, current_token_chars, current_token_normalized)
            if not previous_was_space:
                normalized_text_parts.append(" ")
                previous_was_space = True

        self._flush_current_token(token_groups, current_token_chars, current_token_normalized)
        normalized_text = "".join(normalized_text_parts).strip()
        normalized_text = re.sub(r"\s+", " ", normalized_text)
        return {
            "normalized_text": normalized_text,
            "char_map": char_map,
            "token_groups": token_groups,
        }

    def _is_alignable_char(self, char: str) -> bool:
        return bool(re.match(r"[\u4e00-\u9fffA-Za-z0-9]", char))

    def _normalize_token(self, token: str) -> str:
        normalized = unicodedata.normalize("NFKC", token)
        return normalized.lower() if normalized.isascii() else normalized

    def _flush_current_token(
        self,
        token_groups: List[Dict],
        current_token_chars: List[str],
        current_token_normalized: List[str]
    ) -> None:
        if not current_token_chars:
            return

        token_groups.append({
            "normalized": "".join(current_token_normalized),
            "chars": current_token_chars.copy(),
        })
        current_token_chars.clear()
        current_token_normalized.clear()

    def _handle_fallback(
        self,
        text: str,
        duration: float,
        reason: str
    ) -> List[Dict]:
        if self.fallback_alignment == "uniform":
            print(f"⚠️  {reason}，使用降级方案（均匀时间分配）")
            return self._fallback_alignment(text, duration)

        print(f"⚠️  {reason}，不输出时间戳")
        return []

    def _fallback_alignment(
        self,
        text: str,
        duration: float
    ) -> List[Dict]:
        """
        降级方案: 均匀分配时间
        """
        chars = list(text)
        num_chars = len(chars)

        if num_chars == 0:
            return []

        char_duration = duration / num_chars
        alignments = []

        for i, char in enumerate(chars):
            start = i * char_duration
            end = (i + 1) * char_duration

            alignments.append({
                "char": char,
                "start": round(start, 3),
                "end": round(end, 3),
                "confidence": 0.50  # 降级方案的低置信度
            })

        return alignments
