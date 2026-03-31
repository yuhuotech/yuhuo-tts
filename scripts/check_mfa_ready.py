#!/usr/bin/env python3
"""
检查 MFA 命令、模型和回退策略是否就绪。
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from alignment.mfa_aligner import MFAAligner


def main() -> int:
    aligner = MFAAligner()
    status = aligner.get_status(force_refresh=True)

    print("=" * 60)
    print("MFA Ready Check")
    print("=" * 60)
    print(f"enabled: {status['enabled']}")
    print(f"available: {status['available']}")
    print(f"command_available: {status['command_available']}")
    print(f"command_path: {status['command_path']}")
    print(f"command_error: {status['command_error']}")
    print(f"acoustic_model: {status['acoustic_model']}")
    print(f"acoustic_model_path: {status['acoustic_model_path']}")
    print(f"dictionary: {status['dictionary']}")
    print(f"dictionary_path: {status['dictionary_path']}")
    print(f"fallback_alignment: {status['fallback_alignment']}")
    print(f"reason: {status['reason']}")

    return 0 if status["available"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
