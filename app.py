"""个人知识库系统主应用入口"""

import os
import time
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Callable

# 导入配置和模块
from config import APP_CONFIG, DOCUMENT_DIR, DOCUMENT_CONFIG
from src.document_processor import PDFProcessor, WordProcessor, TextProcessor, URLProcessor
from src.vector_store import ChromaStore
from src.model import create_llm, SentenceEmbedding
from src.utils.helpers import get_document_processor, get_file_extension, get_file_size_str

# 初始化会话状态
if "documents" not in st.session_state:
    st.session_state.documents = []

# 添加刷新标记
if "need_refresh" not in st.session_state:
    st.session_state.need_refresh = False

# 确保embedding_model在初始化后再调用load_model
if "embedding_model" not in st.session_state:
    st.session_state.embedding_model = SentenceEmbedding()
    # 将load_model()调用移到初始化之后的单独检查中

# 确保在embedding_model初始化后再初始化vector_store
if "vector_store" not in st.session_state:
    # 确保embedding_model已经初始化
    if "embedding_model" in st.session_state:
        st.session_state.vector_store = ChromaStore(embedding_function=st.session_state.embedding_model.encode)
    else:
        st.error("初始化向量存储失败：嵌入模型未初始化")

# 在所有初始化完成后，加载模型
if "embedding_model" in st.session_state and st.session_state.embedding_model is not None:
    try:
        st.session_state.embedding_model.load_model()
    except Exception as e:
        st.error(f"加载嵌入模型失败: {str(e)}")

if "model" not in st.session_state:
    st.session_state.model = None
if "use_llm" not in st.session_state:
    st.session_state.use_llm = False

# 重置知识库的二次确认
if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False

# 进度管理相关常量
PROCESS_STAGES = {
    "save_file": {"weight": 0.1, "desc": "保存文件"},
    "init_processor": {"weight": 0.1, "desc": "初始化处理器"},
    "extract_metadata": {"weight": 0.2, "desc": "提取元数据"},
    "process_content": {"weight": 0.4, "desc": "处理内容"},
    "generate_chunks": {"weight": 0.1, "desc": "生成文本块"},
    "vector_store": {"weight": 0.1, "desc": "写入向量库"}
}

def init_progress():
    """初始化进度状态"""
    st.session_state.progress = {
        "current": 0,
        "current_stage": "",
        "stages": PROCESS_STAGES
    }

def update_progress(stage_name: str, progress: float):
    """更新进度回调函数"""
    if not isinstance(stage_name, str):
        raise TypeError(f"stage_name must be a string, got {type(stage_name)}")
        
    if stage_name not in st.session_state.progress["stages"]:
          raise ValueError(f"Invalid stage name: {stage_name}. Valid stages are: {list(st.session_state.progress['stages'].keys())}")
        
    stage = st.session_state.progress["stages"][stage_name]
    stage_keys = list(st.session_state.progress["stages"].keys())
    try:
        stage_index = stage_keys.index(stage_name)
        base_progress = sum(
            st.session_state.progress["stages"][k]["weight"]
            for k in stage_keys[:stage_index]
        )
    except ValueError as e:
        raise ValueError(f"Stage '{stage_name}' not found in progress stages") from e
    
    current_progress = base_progress + progress * stage["weight"]
    st.session_state.progress["current"] = current_progress
    st.session_state.progress["current_stage"] = stage["desc"]

def handle_error(error: Exception, message: str) -> None:
    """统一错误处理"""
    st.error(f"{message}: {str(error)}")
    if 'progress' in st.session_state:
        del st.session_state.progress

def format_metadata(metadata: Dict[str, Any]) -> str:
    """格式化文档元数据"""
    formatted = []
    if metadata.get('source_type') == 'url':
        # URL类型元数据
        if metadata.get('url'):
            formatted.append(f"**URL**: {metadata['url']}")
        formatted.append(f"**来源**: 网页")
    else:
        # 文档类型元数据
        if metadata.get('title'):
            formatted.append(f"**标题**: {metadata['title']}")
        if metadata.get('author'):
            formatted.append(f"**作者**: {metadata['author']}")
        if metadata.get('created'):
            formatted.append(f"**创建时间**: {metadata['created']}")
        if metadata.get('file_size'):
            formatted.append(f"**大小**: {get_file_size_str(metadata['file_size'])}")
    return "\n".join(formatted)

def process_document(uploaded_file):
    """处理上传的文档"""
    try:
        print("开始处理文档:", uploaded_file.name)
        # 保存上传文件
        file_path = os.path.join(DOCUMENT_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        print("文件已保存到:", file_path)
        
        # 获取文档处理器
        processor = get_document_processor(file_path)
        print("文档处理器初始化完成:", type(processor).__name__)
        
        # 初始化进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        progress_data = {"current": 0, "stage": ""}

        # 定义进度更新回调（在主线程执行）
        def update_ui():
            progress_bar.progress(progress_data["current"])
            status_text.text(f"{progress_data['stage']} ({int(progress_data['current']*100)}%)")

        # 设置处理器进度回调（后台线程调用）
        def progress_callback(stage_name, progress):
            # 更新共享进度数据
            try:
                print(f"进度回调: stage_name={stage_name}, progress={progress}")
                stage_keys = list(PROCESS_STAGES.keys())
                # 检查stage_name是否在PROCESS_STAGES中
                if stage_name in PROCESS_STAGES:
                    stage_index = stage_keys.index(stage_name)
                    base_progress = sum(
                        PROCESS_STAGES[k]["weight"]
                        for k in stage_keys[:stage_index]
                    )
                    current_progress = base_progress + progress * PROCESS_STAGES[stage_name]["weight"]
                    stage_desc = PROCESS_STAGES[stage_name]["desc"]
                    print(f"进度计算: base_progress={base_progress}, current_progress={current_progress}, stage_desc={stage_desc}")
                else:
                    # 如果stage_name不在PROCESS_STAGES中，使用默认值
                    current_progress = progress
                    stage_desc = stage_name
                    print(f"未知阶段: {stage_name}, 使用默认进度值: {progress}")
                
                progress_data.update({
                    "current": current_progress,
                    "stage": stage_desc
                })
                print(f"更新进度数据: current={current_progress}, stage={stage_desc}")
                # 直接更新UI，不使用experimental_rerun()
                print("直接更新UI，不使用experimental_rerun()")
                update_ui()
            except Exception as e:
                print(f"Progress callback error: {str(e)}")
                # 继续处理，不中断文档处理流程

        processor.set_progress_callback(progress_callback)
        
        # 启动文档处理
        processor.process(file_path)
        update_ui()  # 最后更新一次进度
        
        
        result = processor.get_result()
        if result is None:
            raise Exception("文档处理失败")
            
        return result
        
    except Exception as e:
        handle_error(e, "文档处理失败")
        return None

def add_to_vector_store(document_data):
    """将文档添加到向量存储"""
    chunks = document_data["chunks"]
    source = document_data["source"]
    metadata = document_data["metadata"]
    
    metadatas = []
    for i, chunk in enumerate(chunks):
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_index"] = i
        chunk_metadata["chunk_count"] = len(chunks)
        chunk_metadata["source"] = source
        metadatas.append(chunk_metadata)
    
    try:
        ids = st.session_state.vector_store.add_texts(chunks, metadatas)
        return ids
    except Exception as e:
        handle_error(e, "添加到向量存储失败")
        return []

def search_documents(query, top_k=5):
    """搜索文档"""
    try:
        results = st.session_state.vector_store.similarity_search(
            query, 
            k=top_k,
            use_llm=st.session_state.use_llm
        )
        return results
    except Exception as e:
        handle_error(e, "搜索失败")
        return []

def generate_answer(query, context):
    """生成回答"""
    if st.session_state.model is None:
        load_model()
    
    try:
        answer = st.session_state.model.generate_response(query, context)
        return answer
    except Exception as e:
        return f"生成回答失败: {str(e)}"

def format_search_results(results):
    """格式化搜索结果为可读文本"""
    if not results:
        return ""
    
    formatted_text = ""
    for i, result in enumerate(results):
        # 跳过LLM生成的结果
        if result['metadata'].get('source') == 'LLM':
            continue
            
        formatted_text += f"### 相似片段 {i+1} (相似度: {result['score']:.2f})\n"
        
        # 根据来源类型显示不同元数据
        if result.get('source_type') == 'url':
            formatted_text += f"**来源**: 网络链接🔗\n"
            if 'url' in result['metadata']:
                formatted_text += f"**URL**: {result['metadata']['url']}\n"
        else:
            formatted_text += f"**来源**: {result['metadata'].get('source', '未知')}\n"
            if 'title' in result['metadata']:
                formatted_text += f"**标题**: {result['metadata']['title']}\n"
        
        # 添加文档位置信息
        if 'chunk_index' in result['metadata'] and 'chunk_count' in result['metadata']:
            formatted_text += f"**位置**: 第 {result['metadata']['chunk_index'] + 1}/{result['metadata']['chunk_count']} 段\n"
        
        # 添加文档特定元数据
        if 'page_count' in result['metadata']:
            formatted_text += f"**总页数**: {result['metadata']['page_count']}\n"
        
        # 显示相似文本片段
        formatted_text += f"\n**相关内容**:\n{result['content']}\n\n"
    
    return formatted_text
    
    return formatted_text

def load_model():
    """加载大模型"""
    if st.session_state.model is None:
        with st.spinner("正在加载模型，请稍候..."):
            st.session_state.model = create_llm()
            st.session_state.model.generate_response("你好")

def process_url(url: str) -> Dict[str, Any]:
    """处理网页链接"""
    try:
        print("开始处理网页链接:", url)
        # 初始化URL处理器
        processor = URLProcessor()
        
        # 初始化进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        progress_data = {"current": 0, "stage": ""}

        # 定义进度更新回调（在主线程执行）
        def update_ui():
            progress_bar.progress(progress_data["current"])
            status_text.text(f"{progress_data['stage']} ({int(progress_data['current']*100)}%)")

        # 设置处理器进度回调（后台线程调用）
        def progress_callback(stage_name, progress):
            try:
                print(f"进度回调: stage_name={stage_name}, progress={progress}")
                stage_keys = list(PROCESS_STAGES.keys())
                if stage_name in PROCESS_STAGES:
                    stage_index = stage_keys.index(stage_name)
                    base_progress = sum(
                        PROCESS_STAGES[k]["weight"]
                        for k in stage_keys[:stage_index]
                    )
                    current_progress = base_progress + progress * PROCESS_STAGES[stage_name]["weight"]
                    stage_desc = PROCESS_STAGES[stage_name]["desc"]
                    print(f"进度计算: base_progress={base_progress}, current_progress={current_progress}, stage_desc={stage_desc}")
                else:
                    current_progress = progress
                    stage_desc = stage_name
                    print(f"未知阶段: {stage_name}, 使用默认进度值: {progress}")
                
                progress_data.update({
                    "current": current_progress,
                    "stage": stage_desc
                })
                print(f"更新进度数据: current={current_progress}, stage={stage_desc}")
                update_ui()
            except Exception as e:
                print(f"Progress callback error: {str(e)}")

        processor.set_progress_callback(progress_callback)
        
        # 处理网页链接
        result = processor.process_url(url)
        update_ui()  # 最后更新一次进度
        
        if result is None:
            raise Exception("网页链接处理失败")
            
        return result
        
    except Exception as e:
        handle_error(e, "网页链接处理失败")
        return None

def render_document_management():
    """渲染文档管理界面"""
    st.header("文档管理")
    
    # 创建两个选项卡：上传文档和网页链接
    tab1, tab2 = st.tabs(["上传文档", "网页链接"])
    
    # 上传文档选项卡
    with tab1:
        uploaded_file = st.file_uploader(
            "上传文档", 
            type=[ext.replace(".", "") for ext in DOCUMENT_CONFIG["supported_formats"]],
            help="支持PDF、Word和TXT格式"
        )
    
    # 网页链接选项卡
    with tab2:
        url = st.text_input(
            "网页链接",
            placeholder="请输入网页链接，例如：https://r.jina.ai/https://zhuanlan.zhihu.com/p/xxxxxx",
            help="支持任何网页链接"
        )
    
    if uploaded_file is not None:
        if st.button("处理文档", key="process_doc"):
            document_data = process_document(uploaded_file)
            
            if document_data:
                print("add_to_vector_store")
                ids = add_to_vector_store(document_data)
                
                if ids:
                    st.session_state.documents.append({
                        "name": uploaded_file.name,
                        "path": os.path.join(DOCUMENT_DIR, uploaded_file.name),
                        "metadata": document_data["metadata"],
                        "total_chunks": len(document_data["chunks"]),
                        "ids": ids
                    })
                    st.success(f"文档 '{uploaded_file.name}' 处理成功，已添加到知识库")
    
    if url:
        if st.button("处理链接", key="process_url"):
            document_data = process_url(url)
            
            if document_data:
                print("add_to_vector_store")
                ids = add_to_vector_store(document_data)
                
                if ids:
                    st.session_state.documents.append({
                        "url": url,
                        "metadata": document_data["metadata"],
                        "total_chunks": len(document_data["chunks"]),
                        "ids": ids
                    })
                    st.success(f"链接 '{url}' 处理成功，已添加到知识库")
    
    if st.session_state.documents:
        st.subheader("已添加的文档")
        for i, doc in enumerate(st.session_state.documents):
            with st.expander(f"{i+1}. {doc.get('name', doc.get('url', '未知'))}", expanded=False):
                st.write(format_metadata(doc['metadata']))
                st.write(f"**分块数**: {doc['total_chunks']}")
                if st.button("删除", key=f"delete_{i}"):
                    st.session_state.vector_store.delete(doc['ids'])
                    st.session_state.documents.pop(i)
                    st.success(f"文档 '{doc.get('name', doc.get('url', '未知'))}' 已删除")
                    st.experimental_rerun()
    else:
        st.info("尚未添加任何文档")
    
    st.subheader("知识库统计")
    doc_count = len(st.session_state.documents)
    chunk_count = st.session_state.vector_store.count()
    st.metric("文档数量", doc_count)
    st.metric("文本块数量", chunk_count)

    if not st.session_state.confirm_reset:
        if st.button("重置知识库", type="primary", help="清空所有文档和向量存储"):
            st.session_state.confirm_reset = True
            st.experimental_rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认重置", type="primary"):
                if st.session_state.documents or st.session_state.vector_store.count() > 0:
                    st.session_state.vector_store.reset()
                    st.session_state.documents = []
                    st.success("知识库已重置")
                else:
                    st.warning("知识库为空，无需重置")
                st.session_state.confirm_reset = False
                st.experimental_rerun()
        with col2:
            if st.button("取消", type="secondary"):
                st.session_state.confirm_reset = False
                st.experimental_rerun()

def render_qa_interface():
    """渲染问答界面"""
    st.header("知识库问答")
    
    # 添加LLM开关
    st.session_state.use_llm = st.checkbox(
        "使用大模型增强搜索",
        value=st.session_state.use_llm,
        help="启用后，搜索结果将包含大模型生成的增强回答"
    )
    
    query = st.text_input("请输入您的问题", placeholder="例如：什么是机器学习？")
    col1, col2 = st.columns([1, 4])
    with col1:
        top_k = st.number_input("检索文档数量", min_value=1, max_value=10, value=3)
    with col2:
        search_btn = st.button("搜索", type="primary", help="从知识库中检索相关文档")
    
    if query and search_btn:
        results = search_documents(query, top_k=top_k)
        
        if results:
            with st.expander("检索结果", expanded=True):
                st.markdown(format_search_results(results))
                
            # 不调用大模型
            if not st.session_state.use_llm:
                return
            
            context = "\n\n".join([result["content"] for result in results])
            
            with st.spinner("正在生成回答..."):
                answer = generate_answer(query, context)
                
            st.subheader("回答")
            st.markdown(answer)
        else:
            st.warning("未找到相关文档，请尝试其他问题或添加更多文档到知识库")

def render_document_browser():
    """渲染文档浏览界面"""
    st.header("文档浏览")
    
    if st.session_state.documents:
        doc_data = []
        for doc in st.session_state.documents:
            print("doc:", doc)
            metadata = doc["metadata"]
            row = {
                "名称": doc.get("matedata", {}).get("title") if doc.get("source_type") == "file" else metadata.get("url", ""),
                "类型": "网络链接" if doc.get("url") !=  "" else "上传文件",
                "分块数": doc["total_chunks"]
            }
            
            if doc.get('source_type', "file") == 'url':
                row["URL"] = metadata.get('url', '')
            else:
                row.update({
                    "大小": get_file_size_str(metadata.get("file_size", 0)),
                    "创建时间": metadata.get("created", ""),
                    "作者": metadata.get("author", "未知")
                })
            
            doc_data.append(row)
        
        st.dataframe(pd.DataFrame(doc_data), use_container_width=True)
    else:
        st.info("尚未添加任何文档，请在侧边栏上传文档")

def main():
    """主函数"""
    st.set_page_config(
        page_title=APP_CONFIG["title"],
        page_icon=APP_CONFIG["icon"],
        layout="wide"
    )
    
    # 检查是否需要刷新页面
    if st.session_state.get("need_refresh", False):
        st.session_state.need_refresh = False
        st.experimental_rerun()
        return
    
    st.title(APP_CONFIG["title"])
    st.markdown(APP_CONFIG["description"])

    # 侧边栏 - 文档管理
    with st.sidebar:
        render_document_management()

    # 主区域 - 知识库问答
    tabs = st.tabs(["知识库问答", "文档浏览"])

    with tabs[0]:
        render_qa_interface()

    with tabs[1]:
        render_document_browser()

    # 页脚
    st.markdown("---")
    st.markdown("📚 个人知识库系统 | 本地化部署 | 数据隐私保护")

if __name__ == "__main__":
    main()
