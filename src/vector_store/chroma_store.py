"""基于Chromadb的向量存储实现"""

import os
import uuid
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
from config import VECTOR_STORE_DIR, VECTOR_STORE_CONFIG, MODEL_CONFIG

# 默认的embedding模型
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class ChromaStore:
    """基于Chromadb的向量存储实现"""

    def __init__(self, collection_name: str = "knowledge_base", embedding_function=None):
        """初始化向量存储

        Args:
            collection_name: 集合名称，默认为knowledge_base
            embedding_function: 嵌入函数，用于将文本转换为向量
        """
        self.collection_name = collection_name
        self.embedding_function = embedding_function or self._default_embedding_function()
        self.embedding_model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
        self.__post_init__()
        
    def _default_embedding_function(self):
        """默认的embedding函数"""
        def embed_function(texts: List[str]) -> List[List[float]]:
            return self.embedding_model.encode(texts).tolist()
        return embed_function

    def __post_init__(self):
        # 初始化Chromadb客户端
        self.client = chromadb.PersistentClient(
            path=VECTOR_STORE_DIR,
            settings=Settings(
                anonymized_telemetry=False,  # 禁用遥测数据收集
                allow_reset=True,
            )
        )
        
        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        except ValueError:
            # 集合不存在，创建新集合
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": VECTOR_STORE_CONFIG["distance_metric"]}
            )
    
    def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """添加文本到向量存储

        Args:
            texts: 要添加的文本列表
            metadatas: 文本对应的元数据列表
            ids: 文本对应的ID列表，如果不提供则自动生成

        Returns:
            添加的文本ID列表
        """
        if not texts:
            return []

        # 如果没有提供ID，则自动生成
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # 确保metadatas与texts长度一致
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]
        
        # 添加文本到集合
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def similarity_search(
        self, 
        query: str, 
        k: int = None,
        filter: Optional[Dict[str, Any]] = None,
        use_llm: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """基于相似度搜索文本

        Args:
            query: 查询文本
            k: 返回的最相似文档数量，默认使用配置文件中的设置
            filter: 过滤条件

        Returns:
            相似文档列表，每个文档包含文本内容、元数据、相似度分数和相似文本片段
        """
        k = k or VECTOR_STORE_CONFIG["top_k"]
        
        # 执行查询
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=filter
        )

        print(results)
        
        # 处理结果
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]
        
        # 组装返回结果
        search_results = []
        for i in range(len(documents)):
            # 提取相关文本片段
            content = documents[i]
            # 计算相似度分数
            similarity_score = 1.0 - distances[i]
            
            # 提取相似文本片段
            similar_text = content
            
            search_results.append({
                "content": content,
                "metadata": metadatas[i],
                "score": similarity_score,
                "id": ids[i],
                "query": query,  # 添加查询文本，用于后续高亮显示
                "similar_text": similar_text,  # 添加相似文本片段
                "distance": distances[i]  # 添加原始距离值
            })
        
        return search_results
    
    def delete(self, ids: List[str]) -> None:
        """删除指定ID的文档

        Args:
            ids: 要删除的文档ID列表
        """
        if not ids:
            return
        
        self.collection.delete(ids=ids)
    
    def update_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: List[str] = None,
        **kwargs
    ) -> List[str]:
        """更新文本

        Args:
            texts: 要更新的文本列表
            metadatas: 文本对应的元数据列表
            ids: 文本对应的ID列表，必须提供

        Returns:
            更新的文本ID列表
        """
        if not texts or not ids:
            return []
        
        # 确保metadatas与texts长度一致
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]
        
        # 先删除旧文档
        self.delete(ids)
        
        # 添加新文档
        return self.add_texts(texts, metadatas, ids)
    
    def get(self, ids: List[str]) -> Dict[str, Any]:
        """获取指定ID的文档

        Args:
            ids: 要获取的文档ID列表

        Returns:
            文档内容、元数据和ID
        """
        if not ids:
            return {"documents": [], "metadatas": [], "ids": []}
        
        results = self.collection.get(ids=ids)
        
        return {
            "documents": results.get("documents", []),
            "metadatas": results.get("metadatas", []),
            "ids": results.get("ids", [])
        }
    
    def count(self) -> int:
        """获取集合中的文档数量

        Returns:
            文档数量
        """
        return self.collection.count()
    
    def reset(self) -> None:
        """重置集合，删除所有文档"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": VECTOR_STORE_CONFIG["distance_metric"]}
        )
