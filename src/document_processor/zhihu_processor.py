"""知乎文章处理模块，负责处理知乎文章内容"""

import os
from typing import List, Dict, Any, Optional, Callable
from config import DOCUMENT_CONFIG, DOCUMENT_DIR
from src.utils.zhihu_crawler import ZhihuCrawler
from .text_processor import TextProcessor


class ZhihuProcessor(TextProcessor):
    """知乎文章处理器，用于处理知乎文章链接"""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """初始化知乎文章处理器

        Args:
            chunk_size: 文档分块大小，默认使用配置文件中的设置
            chunk_overlap: 分块重叠大小，默认使用配置文件中的设置
        """
        super().__init__(chunk_size, chunk_overlap)
        self.crawler = ZhihuCrawler()
    
    def process_url(self, url: str) -> Dict[str, Any]:
        """处理知乎文章链接，提取内容并分块

        Args:
            url: 知乎文章链接

        Returns:
            包含文本块和元数据的字典
        """
        # 验证URL
        if not self.crawler.validate_url(url):
            raise ValueError(f"无效的知乎文章链接: {url}")
        
        # 提取文章内容
        if self.progress_callback:
            self.progress_callback("process_content", 0.3)
            
        article_data = self.crawler.extract_article(url)
        if not article_data:
            raise Exception(f"提取知乎文章内容失败: {url}")
            
        if self.progress_callback:
            self.progress_callback("process_content", 0.6)
        
        # 保存为文本文件
        file_path = self.crawler.save_as_text(article_data, DOCUMENT_DIR)
        
        if self.progress_callback:
            self.progress_callback("process_content", 1.0)
            
        # 使用TextProcessor处理文本文件
        result = self.process(file_path)
        
        # 添加知乎特有的元数据
        result["metadata"]["title"] = article_data["title"]
        result["metadata"]["author"] = article_data["author"]
        result["metadata"]["url"] = article_data["url"]
        result["metadata"]["source_type"] = "zhihu"
        
        return result