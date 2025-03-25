"""PDF文档处理模块，负责解析PDF文档并提取文本内容"""

import os
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Callable
from config import DOCUMENT_CONFIG


from .base_processor import BaseProcessor

class PDFProcessor(BaseProcessor):
    """PDF文档处理器，用于解析PDF文档并提取文本内容"""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """初始化PDF处理器

        Args:
            chunk_size: 文档分块大小，默认使用配置文件中的设置
            chunk_overlap: 分块重叠大小，默认使用配置文件中的设置
        """
        super().__init__(chunk_size, chunk_overlap)
        self._result = None

    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """设置进度回调函数
        
        Args:
            callback: 回调函数，接受阶段名称和进度比例两个参数
        """
        self.progress_callback = callback

    def extract_text(self, file_path: str) -> str:
        """从PDF文件中提取全部文本

        Args:
            file_path: PDF文件路径

        Returns:
            提取的文本内容
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            print(f"开始从PDF提取文本: {file_path}")
            # 打开PDF文件
            doc = fitz.open(file_path)
            text = ""
            total_pages = len(doc)
            print(f"PDF总页数: {total_pages}")

            # 遍历所有页面并提取文本
            for i, page in enumerate(doc):
                print(f"处理第 {i+1}/{total_pages} 页")
                page_text = page.get_text()
                text += page_text
                text += "\n\n"  # 添加页面分隔符
                print(f"第 {i+1} 页文本长度: {len(page_text)}字符")
                
                # 更新进度
                if self.progress_callback:
                    progress = (i + 1) / total_pages
                    print(f"调用进度回调: process_content, {progress:.2f}")
                    self.progress_callback("process_content", progress)

            doc.close()
            print(f"PDF文本提取完成，总长度: {len(text)}字符")
            return text
        except Exception as e:
            raise Exception(f"PDF文件解析失败: {str(e)}")

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取PDF文件的元数据

        Args:
            file_path: PDF文件路径

        Returns:
            元数据字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            doc = fitz.open(file_path)
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "page_count": len(doc),
                "file_size": os.path.getsize(file_path),
            }
            doc.close()
            return metadata
        except Exception as e:
            raise Exception(f"PDF元数据提取失败: {str(e)}")



        return chunks

    def process(self, file_path: str) -> Dict[str, Any]:
        """处理PDF文件，提取文本并分块

        Args:
            file_path: PDF文件路径

        Returns:
            包含文本块和元数据的字典
        """
        try:
            print(f"开始处理PDF文件: {file_path}")
            print(f"进度回调函数是否设置: {self.progress_callback is not None}")
            
            # 初始化处理结果
            self._result = {
                "source": file_path,
                "metadata": {},
                "chunks": []
            }
            
            # 提取元数据
            print("开始提取元数据...")
            if self.progress_callback:
                print("调用进度回调: extract_metadata, 0.5")
                self.progress_callback("extract_metadata", 0.5)
            self._result["metadata"] = self.extract_metadata(file_path)
            print(f"元数据提取完成: {self._result['metadata']}")
            if self.progress_callback:
                print("调用进度回调: extract_metadata, 1.0")
                self.progress_callback("extract_metadata", 1.0)
            
            # 处理内容
            print("开始提取文本内容...")
            text = self.extract_text(file_path)
            print(f"文本提取完成，长度: {len(text)}字符")
            
            # 生成文本块
            print("开始生成文本块...")
            if self.progress_callback:
                print("调用进度回调: generate_chunks, 0.5")
                self.progress_callback("generate_chunks", 0.5)
            self._result["chunks"] = self.chunk_text(text)
            print(f"文本块生成完成，共{len(self._result['chunks'])}个块")
            if self.progress_callback:
                print("调用进度回调: generate_chunks, 1.0")
                self.progress_callback("generate_chunks", 1.0)
            
            print("PDF处理完成")
            return self._result
            
        except Exception as e:
            self._result = None
            raise e

    def get_result(self) -> Optional[Dict[str, Any]]:
        """获取处理结果"""
        return self._result
