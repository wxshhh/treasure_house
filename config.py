"""配置文件，存储应用的各种配置参数"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.absolute()

# 数据存储目录
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCUMENT_DIR = os.path.join(DATA_DIR, "documents")
VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")

# 确保目录存在
os.makedirs(DOCUMENT_DIR, exist_ok=True)
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

# 模型配置
MODEL_CONFIG = {
    "model_name": "Qwen/Qwen-7B",  # 模型名称
    "device": "cpu",  # 运行设备，可选 "cpu" 或 "cuda"
    "max_length": 2048,  # 最大生成长度
    "temperature": 0.7,  # 生成温度
    "top_p": 0.9,  # Top-p 采样
    "enable_llm": True,  # 是否启用LLM能力
    "llm_provider": "ollama",  # LLM调用方式，可选 "qwen" 或 "ollama"
    "ollama_config": {
        "base_url": "http://localhost:11434",  # ollama服务地址
        "model_name": "llama3.2:latest"  # ollama模型名称
    }
}

# 文档处理配置
DOCUMENT_CONFIG = {
    "chunk_size": 1000,  # 文档分块大小
    "chunk_overlap": 50,  # 分块重叠大小
    "supported_formats": [".pdf", ".docx", ".txt"],  # 支持的文档格式
}

# 向量存储配置
VECTOR_STORE_CONFIG = {
    "embedding_dimension": 768,  # 嵌入向量维度
    "distance_metric": "cosine",  # 距离度量方式
    "top_k": 5,  # 检索时返回的最相似文档数量
}

# Streamlit 应用配置
APP_CONFIG = {
    "title": "个人知识库系统",
    "description": "本地化部署的个人知识库系统，专注于数据隐私保护和轻量级运行",
    "port": 8501,
    "icon": "📚",  # 使用书籍emoji作为应用图标
}
