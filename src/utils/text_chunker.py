"""文本分块器，实现智能分块策略"""

import re
import jieba
from typing import List, Optional
from config import DOCUMENT_CONFIG


class TextChunker:
    """文本分块器，实现段落优先的分块策略"""
    
    def __init__(self, 
                 chunk_size: int = DOCUMENT_CONFIG["chunk_size"],
                 chunk_overlap: int = DOCUMENT_CONFIG["chunk_overlap"]):
        """初始化分块器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def split_text(self, text: str) -> List[str]:
        """将文本分割成块
        
        Args:
            text: 要分割的文本
            
        Returns:
            分割后的文本块列表
        """
        # 首先按段落分割
        paragraphs = self._split_paragraphs(text)
        
        # 处理段落
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # 如果段落本身超过chunk_size，需要进一步分割
            if len(para) > self.chunk_size:
                # 将长段落分割成句子
                sentences = self._split_sentences(para)
                # 处理句子
                for sent in sentences:
                    if len(current_chunk) + len(sent) <= self.chunk_size:
                        current_chunk += sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sent
            else:
                # 如果添加整个段落后超过chunk_size
                if len(current_chunk) + len(para) > self.chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = para
                else:
                    current_chunk += para
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        # 处理重叠
        if self.chunk_overlap > 0:
            chunks = self._add_overlap(chunks)
            
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """将文本按段落分割
        
        Args:
            text: 要分割的文本
            
        Returns:
            段落列表
        """
        # 使用多个换行符作为段落分隔符
        paragraphs = re.split(r'\n\s*\n', text)
        # 过滤空段落并确保每个段落以换行符结尾
        return [p.strip() + '\n' for p in paragraphs if p.strip()]
    
    def _split_sentences(self, text: str) -> List[str]:
        """将文本分割成句子
        
        Args:
            text: 要分割的文本
            
        Returns:
            句子列表
        """
        # 使用jieba分词进行中文分句
        text = text.replace('\n', '')
        sentences = []
        
        # 使用正则表达式匹配句子结束符
        pattern = r'([。！？!?]+|\\n)'
        
        # 先用结束符分割
        parts = re.split(pattern, text)
        
        # 重新组合句子
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and re.match(pattern, parts[i + 1]):
                sentences.append(parts[i] + parts[i + 1])
                i += 2
            else:
                if parts[i].strip():
                    sentences.append(parts[i])
                i += 1
        
        return sentences
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """为文本块添加重叠
        
        Args:
            chunks: 文本块列表
            
        Returns:
            处理后的文本块列表
        """
        if not chunks:
            return chunks
            
        result = [chunks[0]]
        
        for i in range(1, len(chunks)):
            # 获取前一个chunk的末尾部分
            prev_chunk = chunks[i-1]
            overlap = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            
            # 将重叠部分添加到当前chunk的开头
            current_chunk = chunks[i]
            result.append(overlap + current_chunk)
            
        return result