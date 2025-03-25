"""嵌入模型模块，负责生成文本的向量表示"""

import os
import torch
import numpy as np
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModel
from config import VECTOR_STORE_CONFIG


class SentenceEmbedding:
    """句子嵌入模型，用于生成文本的向量表示"""

    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese"):
        """初始化句子嵌入模型

        Args:
            model_name: 模型名称，默认使用text2vec-base-chinese
        """
        self.model_name = model_name
        self.dimension = VECTOR_STORE_CONFIG["embedding_dimension"]
        
        # 延迟加载模型，避免在初始化时就占用大量内存
        self.tokenizer = None
        self.model = None
    
    def load_model(self):
        """加载模型和分词器"""
        if self.tokenizer is None or self.model is None:
            try:
                print(f"正在加载嵌入模型: {self.model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name)
                # 将模型设置为评估模式
                self.model.eval()
                print("嵌入模型加载完成")
            except Exception as e:
                raise Exception(f"嵌入模型加载失败: {str(e)}")
    
    def _mean_pooling(self, model_output, attention_mask):
        """平均池化，将token级别的向量转换为句子级别的向量

        Args:
            model_output: 模型输出
            attention_mask: 注意力掩码

        Returns:
            句子向量
        """
        # 获取token嵌入
        token_embeddings = model_output[0]
        
        # 扩展注意力掩码
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        # 对token嵌入进行掩码和求和
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        # 计算平均值
        return sum_embeddings / sum_mask
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """将文本编码为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        # 确保模型已加载
        if self.tokenizer is None or self.model is None:
            self.load_model()
        
        # 对空列表进行处理
        if not texts:
            return []
        
        try:
            # 对文本进行编码
            encoded_input = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=512)
            
            # 不计算梯度
            with torch.no_grad():
                model_output = self.model(**encoded_input)
            
            # 计算句子嵌入
            sentence_embeddings = self._mean_pooling(model_output, encoded_input["attention_mask"])
            
            # 归一化嵌入
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
            
            # 转换为列表
            return sentence_embeddings.tolist()
        except Exception as e:
            print(f"生成嵌入向量失败: {str(e)}")
            # 返回零向量作为后备
            return [[0.0] * self.dimension] * len(texts)
    
    def encode_query(self, query: str) -> List[float]:
        """将查询文本编码为向量

        Args:
            query: 查询文本

        Returns:
            查询向量
        """
        embeddings = self.encode([query])
        return embeddings[0] if embeddings else [0.0] * self.dimension