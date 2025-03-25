"""文档处理模块，负责解析不同格式的文档并提取文本内容"""

from .pdf_processor import PDFProcessor
from .word_processor import WordProcessor
from .text_processor import TextProcessor
from .zhihu_processor import ZhihuProcessor

__all__ = ["PDFProcessor", "WordProcessor", "TextProcessor", "ZhihuProcessor"]