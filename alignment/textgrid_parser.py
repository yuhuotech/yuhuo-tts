"""TextGrid文件解析和字幕生成"""

from typing import List, Dict
import re

class TextGridParser:
    """TextGrid格式解析器"""

    @staticmethod
    def parse_file(filepath: str) -> List[Dict]:
        """
        解析TextGrid文件

        Args:
            filepath: TextGrid文件路径

        Returns:
            时间戳列表: [{"char": "你", "start": 0.0, "end": 0.45}, ...]
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            return TextGridParser._parse_content(content)
        except Exception as e:
            print(f"解析TextGrid失败: {str(e)}")
            return []

    @staticmethod
    def _parse_content(content: str) -> List[Dict]:
        """解析TextGrid内容"""

        intervals = []

        # 正则表达式匹配intervals
        pattern = r'intervals\s*\[\d+\]\s*:\s*xmin\s*=\s*([\d.]+)\s*xmax\s*=\s*([\d.]+)\s*text\s*=\s*"([^"]*)"'

        matches = re.finditer(pattern, content)

        for match in matches:
            xmin = float(match.group(1))
            xmax = float(match.group(2))
            text = match.group(3).strip()

            if text and text not in ['<sil>', '<silence>']:
                intervals.append({
                    "char": text,
                    "start": round(xmin, 3),
                    "end": round(xmax, 3),
                    "confidence": 0.88
                })

        return intervals

class SRTGenerator:
    """SRT字幕生成"""

    @staticmethod
    def generate(alignments: List[Dict], output_path: str = "output.srt") -> str:
        """
        生成SRT格式字幕

        Args:
            alignments: 时间戳列表
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        srt_content = ""

        for idx, alignment in enumerate(alignments, 1):
            start = TextGridParser._seconds_to_srt_time(alignment['start'])
            end = TextGridParser._seconds_to_srt_time(alignment['end'])

            srt_content += f"{idx}\n"
            srt_content += f"{start} --> {end}\n"
            srt_content += f"{alignment['char']}\n\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        return output_path

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

class VTTGenerator:
    """VTT字幕生成"""

    @staticmethod
    def generate(alignments: List[Dict], output_path: str = "output.vtt") -> str:
        """
        生成VTT格式字幕

        Args:
            alignments: 时间戳列表
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        vtt_content = "WEBVTT\n\n"

        for alignment in alignments:
            start = TextGridParser._seconds_to_vtt_time(alignment['start'])
            end = TextGridParser._seconds_to_vtt_time(alignment['end'])

            vtt_content += f"{start} --> {end}\n"
            vtt_content += f"{alignment['char']}\n\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vtt_content)

        return output_path

    @staticmethod
    def _seconds_to_vtt_time(seconds: float) -> str:
        """将秒数转换为VTT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
