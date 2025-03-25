"""工具函数模块，提供通用的辅助功能"""

import os
from typing import Optional, Dict, Any
from config import DOCUMENT_CONFIG


def get_file_extension(file_path: str) -> str:
    """获取文件扩展名

    Args:
        file_path: 文件路径

    Returns:
        文件扩展名（小写，包含点号）
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower()


def get_document_processor(file_path: str):
    """根据文件扩展名获取对应的文档处理器

    Args:
        file_path: 文件路径

    Returns:
        文档处理器实例

    Raises:
        ValueError: 如果文件格式不支持
    """
    from src.document_processor import PDFProcessor, WordProcessor, TextProcessor
    
    ext = get_file_extension(file_path)
    
    # 检查文件格式是否支持
    if ext not in DOCUMENT_CONFIG["supported_formats"]:
        raise ValueError(f"不支持的文件格式: {ext}，支持的格式: {DOCUMENT_CONFIG['supported_formats']}")
    
    # 根据文件扩展名选择处理器
    if ext == ".pdf":
        return PDFProcessor()
    elif ext == ".docx":
        return WordProcessor()
    elif ext == ".txt":
        return TextProcessor()
    else:
        raise ValueError(f"未找到处理器: {ext}")


def format_metadata(metadata: Dict[str, Any]) -> str:
    """格式化元数据为可读字符串

    Args:
        metadata: 元数据字典

    Returns:
        格式化后的元数据字符串
    """
    formatted = []
    for key, value in metadata.items():
        if value:
            formatted.append(f"{key}: {value}")
    
    return "\n".join(formatted)


def get_file_size_str(size_in_bytes: int) -> str:
    """将文件大小转换为可读字符串

    Args:
        size_in_bytes: 文件大小（字节）

    Returns:
        格式化后的文件大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0 or unit == 'GB':
            break
        size_in_bytes /= 1024.0
    
    return f"{size_in_bytes:.2f} {unit}"