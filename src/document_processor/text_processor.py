"""纯文本处理模块，负责解析TXT文档并提取文本内容"""

import os
from typing import List, Dict, Any, Optional, Callable
from config import DOCUMENT_CONFIG


from .base_processor import BaseProcessor

class TextProcessor(BaseProcessor):
    """文本处理器，用于处理纯文本文件"""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """初始化文本处理器

        Args:
            chunk_size: 文档分块大小，默认使用配置文件中的设置
            chunk_overlap: 分块重叠大小，默认使用配置文件中的设置
        """
        super().__init__(chunk_size, chunk_overlap)

    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """设置进度回调函数
        
        Args:
            callback: 回调函数，接受当前进度和总进度两个参数
        """
        self.progress_callback = callback

    def extract_text(self, file_path: str) -> str:
        """从文本文件中提取全部文本

        Args:
            file_path: 文本文件路径

        Returns:
            提取的文本内容
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            # 打开文本文件
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return text
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    text = file.read()
                return text
            except Exception as e:
                raise Exception(f"文本文件解析失败: {str(e)}")
        except Exception as e:
            raise Exception(f"文本文件解析失败: {str(e)}")

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取文本文件的元数据

        Args:
            file_path: 文本文件路径

        Returns:
            元数据字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            # 对于纯文本文件，元数据较少
            metadata = {
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                "created": os.path.getctime(file_path),
                "modified": os.path.getmtime(file_path),
            }
            return metadata
        except Exception as e:
            raise Exception(f"文本元数据提取失败: {str(e)}")



    def process(self, file_path: str) -> Dict[str, Any]:
        """处理文本文件，提取文本并分块

        Args:
            file_path: 文本文件路径

        Returns:
            包含文本块和元数据的字典
        """
        text = self.extract_text(file_path)
        print("extract_text")
        chunks = self.chunk_text(text)
        print("chunk_text")
        metadata = self.extract_metadata(file_path)
        print("extract_metadata")
        
        print("+++++++++++++")
        print(text)

        # 保存处理结果到实例变量
        self.result = {
            "chunks": chunks,
            "metadata": metadata,
            "source": file_path,
            "source_type": "file",
            "total_chunks": len(chunks),
        }
        return self.result

    def get_result(self) -> Optional[Dict[str, Any]]:
        """获取处理结果"""
        print("-----------")
        print(self)
        return getattr(self, 'result', None)
