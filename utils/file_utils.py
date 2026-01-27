"""文件处理工具"""

import os
import json
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

def ensure_dir(path: str) -> str:
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
    return path

def get_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_json(data: dict, filepath: str, indent: int = 2) -> str:
    """保存JSON文件"""
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    return filepath

def load_json(filepath: str) -> dict:
    """加载JSON文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_file_url(file_id: str, base_url: str = "http://localhost:8000") -> str:
    """获取文件URL"""
    return f"{base_url}/audio/{file_id}.wav"

def list_files(directory: str, extension: str = None) -> list:
    """列出目录中的文件"""
    files = []
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            if extension is None or item.endswith(extension):
                files.append(item)
    return sorted(files)

def delete_file(filepath: str) -> bool:
    """删除文件"""
    try:
        os.remove(filepath)
        return True
    except Exception as e:
        print(f"删除文件失败: {str(e)}")
        return False

def clean_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """清理临时文件"""
    from time import time
    current_time = time()
    deleted_count = 0
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_age = (current_time - os.path.getmtime(filepath)) / 3600
            if file_age > max_age_hours:
                if delete_file(filepath):
                    deleted_count += 1
    return deleted_count
