"""URL处理模块，负责处理网页内容"""

import os
import requests
from typing import List, Dict, Any, Optional, Callable
from urllib.parse import urlparse
from .base_processor import BaseProcessor


class URLProcessor(BaseProcessor):
    """URL处理器，用于处理网页链接"""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """初始化URL处理器

        Args:
            chunk_size: 文档分块大小，默认使用配置文件中的设置
            chunk_overlap: 分块重叠大小，默认使用配置文件中的设置
        """
        super().__init__(chunk_size, chunk_overlap)

    def extract_text(self, url: str) -> str:
        """从网页链接提取文本内容

        Args:
            url: 网页链接

        Returns:
            提取的markdown格式文本内容
        """
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"无效的网页链接: {url}")

        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url)
        response.raise_for_status()
        return response.text

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """提取网页的元数据

        Args:
            url: 网页链接

        Returns:
            元数据字典
        """
        return {
            "url": url,
            "source_type": "url"
        }

    def process_url(self, url: str) -> Dict[str, Any]:
        """处理网页链接，提取内容并分块

        Args:
            url: 网页链接

        Returns:
            包含文本块和元数据的字典
        """
        if self.progress_callback:
            self.progress_callback("开始处理", 0.0)

        text = self.extract_text(url)
        if self.progress_callback:
            self.progress_callback("文本提取完成", 0.3)

        metadata = self.extract_metadata(url)
        if self.progress_callback:
            self.progress_callback("元数据提取完成", 0.6)

        chunks = self.chunk_text(text)
        if self.progress_callback:
            self.progress_callback("分块完成", 1.0)

        return {
            "chunks": chunks,
            "metadata": metadata,
            "source": url,
            "source_type": "url",
            "total_chunks": len(chunks)
        }
