# 个人知识库系统

这是一个本地化部署的个人知识库系统，专注于数据隐私保护和轻量级运行。

## 核心特点

- **本地化部署**：所有数据存储在本地，确保隐私安全
- **轻量级运行**：降低对主机性能的依赖
- **多格式支持**：支持Word、PDF、TXT等常见文档类型
- **检索与问答结合**：通过知识库检索增强大模型回答的准确性
- **知乎文章支持**：支持导入知乎文章到知识库

## 系统架构

```
主机（本地部署）
├─ Qwen-7B模型（离线运行）
├─ Chromadb（存储文档向量）
├─ 文档解析器（处理PDF/Word/TXT/知乎文章）
└─ 前端界面（Streamlit）
```

## 组件选型

| 组件 | 选型 | 理由 |
| --- | --- | --- |
| 大模型 | Qwen-7B（通义千问 7B） | 开源、本地化部署、支持多语言（含中文）、推理效率高 |
| 文档检索 | Chromadb | 纯Python实现，无需外部依赖，支持全文检索和增量更新 |
| 文件解析 | PyMuPDF + python-docx + requests | 轻量级库，支持高效解析文档内容和知乎文章 |
| 界面交互 | Streamlit | 快速搭建Web界面，支持文件上传、检索和问答交互 |

## 文本分片策略

系统采用智能分片策略，确保文本块的语义完整性和检索效果：

### 段落优先分割

- 首先按段落（多个换行符）分割文本
- 保持段落的完整性，避免破坏文本语义结构
- 对超长段落进行进一步处理

### 句子级动态分割

- 使用中文分句规则（句号、感叹号、问号等）切分超长段落
- 动态合并短句，避免过度分割
- 保持句子的完整性，提高检索准确度

### 重叠策略

- 块与块之间保持适度重叠
- 默认重叠比例可通过配置调整

## 知乎文章处理

系统支持通过链接导入知乎文章到知识库：

- 自动提取文章标题、作者、发布时间等元数据
- 智能分段处理文章内容
- 支持批量导入多篇文章
- 减少文本分割导致的语义断裂

### 配置示例

```python
# config.py
DOCUMENT_CONFIG = {
    "chunk_size": 500,     # 文本块大小
    "chunk_overlap": 50   # 重叠大小
}

# 使用示例
from utils.text_chunker import TextChunker

chunker = TextChunker(chunk_size=500, chunk_overlap=50)
text_chunks = chunker.split_text(document_text)
```

## 使用方法

1. 安装依赖：`pip install -r requirements.txt`
2. 启动应用：`python app.py`
3. 在浏览器中访问：`http://localhost:8501`

## 项目结构

```
./
├── app.py                 # 主应用入口
├── requirements.txt       # 项目依赖
├── README.md              # 项目说明
├── config.py              # 配置文件
├── data/                  # 数据存储目录
│   ├── documents/         # 原始文档存储
│   └── vector_store/      # 向量数据库存储
└── src/                   # 源代码
    ├── document_processor/ # 文档处理模块
    │   ├── __init__.py
    │   ├── pdf_processor.py
    │   ├── word_processor.py
    │   └── text_processor.py
    ├── vector_store/      # 向量存储模块
    │   ├── __init__.py
    │   └── chroma_store.py
    ├── model/             # 模型模块
    │   ├── __init__.py
    │   └── llm.py
    └── utils/             # 工具函数
        ├── __init__.py
        └── helpers.py
```