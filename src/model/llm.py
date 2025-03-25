"""大模型模块，支持多种LLM调用方式"""

import os
import torch
import requests
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from transformers import AutoTokenizer, AutoModelForCausalLM
from config import MODEL_CONFIG


class BaseLLM(ABC):
    """LLM抽象基类，定义统一接口"""
    
    @abstractmethod
    def generate_response(self, query: str, context: Optional[str] = None) -> str:
        """生成回答"""
        pass
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入"""
        pass


class QwenLLM(BaseLLM):
    """Qwen模型封装，用于加载和使用Qwen-7B模型进行问答"""

    def __init__(self, model_name: str = None, device: str = None):
        """初始化Qwen模型

        Args:
            model_name: 模型名称，默认使用配置文件中的设置
            device: 运行设备，默认使用配置文件中的设置
        """
        self.model_name = model_name or MODEL_CONFIG["model_name"]
        self.device = device or MODEL_CONFIG["device"]
        self.max_length = MODEL_CONFIG["max_length"]
        self.temperature = MODEL_CONFIG["temperature"]
        self.top_p = MODEL_CONFIG["top_p"]
        
        # 延迟加载模型
        self.tokenizer = None
        self.model = None
    
    def load_model(self):
        """加载模型和分词器"""
        if self.tokenizer is None or self.model is None:
            try:
                print(f"正在加载模型: {self.model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map=self.device,
                    trust_remote_code=True,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                print("模型加载完成")
            except Exception as e:
                raise Exception(f"模型加载失败: {str(e)}")
    
    def generate_response(self, query: str, context: Optional[str] = None) -> str:
        """生成回答"""
        if self.tokenizer is None or self.model is None:
            self.load_model()
        
        try:
            prompt = f"以下是一些相关的知识：\n{context}\n\n根据上述知识，请回答问题：{query}" if context else query
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_length=self.max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if context:
                response = response.split("根据上述知识，请回答问题：")[-1].strip()
                response = response.split(query)[-1].strip()
            elif response.startswith(query):
                response = response[len(query):].strip()
            
            return response
        except Exception as e:
            return f"生成回答时出错: {str(e)}"
    
    def generate_embedding(self, text: str) -> List[float]:
        raise NotImplementedError("Qwen-7B模型不直接支持生成嵌入向量")


class OllamaLLM(BaseLLM):
    """Ollama API封装，用于调用本地部署的Ollama服务"""

    def __init__(self):
        self.base_url = MODEL_CONFIG["ollama_config"]["base_url"]
        self.model_name = MODEL_CONFIG["ollama_config"]["model_name"]
    
    def generate_response(self, query: str, context: Optional[str] = None) -> str:
        """通过Ollama API生成回答"""
        try:
            prompt = f"以下是一些相关的知识：\n{context}\n\n根据上述知识，请回答问题：{query}" if context else query
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": MODEL_CONFIG["temperature"],
                        "top_p": MODEL_CONFIG["top_p"],
                        "num_ctx": MODEL_CONFIG["max_length"]
                    }
                }
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            return f"Ollama API调用失败: {str(e)}"
    
    def generate_embedding(self, text: str) -> List[float]:
        """通过Ollama API生成嵌入向量"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                }
            )
            response.raise_for_status()
            return response.json().get("embedding", [])
        except Exception as e:
            raise Exception(f"Ollama嵌入生成失败: {str(e)}")


def create_llm() -> BaseLLM:
    """LLM工厂方法，根据配置创建对应的LLM实例"""
    provider = MODEL_CONFIG.get("llm_provider", "qwen")
    if provider == "ollama":
        return OllamaLLM()
    return QwenLLM()
