"""文档处理器基类，提供通用的文本分片功能"""

from typing import List, Dict, Any, Optional, Callable
from config import DOCUMENT_CONFIG
from src.utils.text_chunker import TextChunker

class BaseProcessor:
    """文档处理器基类"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """初始化处理器
        
        Args:
            chunk_size: 文档分块大小，默认使用配置文件中的设置
            chunk_overlap: 分块重叠大小，默认使用配置文件中的设置
        """
        self.chunk_size = chunk_size or DOCUMENT_CONFIG["chunk_size"]
        self.chunk_overlap = chunk_overlap or DOCUMENT_CONFIG["chunk_overlap"]
        self.progress_callback = None
        self.chunker = TextChunker(self.chunk_size, self.chunk_overlap)
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """设置进度回调函数
        
        Args:
            callback: 回调函数，接受阶段名称和进度值两个参数
        """
        self.progress_callback = callback
    
    def chunk_text(self, text: str) -> List[str]:
        """将文本分割成块
        
        Args:
            text: 要分割的文本
            
        Returns:
            文本块列表
        """
        if not text:
            return []
            
        # 使用TextChunker进行分片
        chunks = self.chunker.split_text(text)
        
        # 更新进度
        if self.progress_callback:
            self.progress_callback("generate_chunks", 1.0)
            
        return chunks