import os
import chromadb
import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Message
from .models import get_all_policies

# ==================== 阿里云 API 配置区域 ====================
# 方式1：直接在下方填写你的阿里云 API Key（推荐用于快速测试）
# 请访问 https://dashscope.aliyun.com/ 获取 API Key
ALI_API_KEY = "sk-2b10a4ce860f4db09c7ee09571bb74ac"  # <-- 在这里填写你的阿里云 API Key，例如："sk-xxxxxxxxxxxxxxxx"

# 方式2：使用环境变量（推荐用于生产环境）
# 在终端中运行：$env:ALI_API_KEY="你的API密钥" (PowerShell)
# 或在 CMD 中运行：set ALI_API_KEY=你的API密钥
# ============================================================

# 阿里云 DashScope 配置
EMBEDDING_MODEL = "text-embedding-v2"  # 阿里云文本嵌入模型
LLM_MODEL = "qwen-turbo"  # 阿里云通义千问模型
TOP_K = 5

CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'chroma.db')

chromadb_client = chromadb.PersistentClient(CHROMA_DB_PATH)
chromadb_collection = chromadb_client.get_or_create_collection("policy_data")

# 配置阿里云 API Key
if ALI_API_KEY:
    # 优先使用代码中直接填写的 API Key
    dashscope.api_key = ALI_API_KEY
    print("[OK] 已使用代码中配置的阿里云 API Key")
else:
    # 尝试从环境变量读取
    try:
        dashscope.api_key = os.environ["ALI_API_KEY"]
        print("[OK] 已使用环境变量中的阿里云 API Key")
    except KeyError:
        print("[WARNING] 未能找到阿里云 API Key。")
        print("   请在 app/rag.py 文件中填写 ALI_API_KEY，或设置环境变量。")
        print("   访问 https://dashscope.aliyun.com/ 获取 API Key")

def embed(text: str, is_document: bool = True) -> list[float]:
    """使用阿里云 DashScope 进行文本嵌入"""
    from dashscope import TextEmbedding
    
    resp = TextEmbedding.call(
        model=EMBEDDING_MODEL,
        input=text
    )
    
    if resp.status_code == 200:
        return resp.output['embeddings'][0]['embedding']
    else:
        raise Exception(f"嵌入失败: {resp.message}")

def get_chunks_from_policies():
    policies = get_all_policies()
    chunks = []
    for policy in policies:
        content = policy['content']
        policy_chunks = content.split('\n\n')
        for chunk in policy_chunks:
            if chunk.strip():
                chunks.append(f"政策标题: {policy['title']}\n{chunk}")
    return chunks

def create_rag_db():
    chunks = get_chunks_from_policies()
    for idx, chunk in enumerate(chunks):
        embedding = embed(chunk)
        chromadb_collection.upsert(
            ids=str(idx),
            documents=chunk,
            embeddings=embedding
        )
    return len(chunks)

def query_rag_db(query: str):
    question_embedding = embed(query)
    result = chromadb_collection.query(
        query_embeddings=question_embedding,
        n_results=TOP_K
    )
    return result["documents"][0]

def generate_answer(question: str):
    try:
        find_chunks = query_rag_db(question)
        
        # 构建系统提示词
        system_prompt = "你是一个政策问答助手，请根据提供的上下文准确回答用户的问题。如果上下文中没有相关信息，请说明无法回答。"
        
        # 构建用户提示词
        user_prompt = f"问题：{question}\n\n上下文：\n"
        for c in find_chunks:
            user_prompt += f"{c}\n---------\n"
        
        # 调用阿里云通义千问
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        response = Generation.call(
            model=LLM_MODEL,
            messages=messages,
            result_format='message'
        )
        
        if response.status_code == 200:
            answer = response.output.choices[0]['message']['content']
            return answer, find_chunks
        else:
            return f"生成回答失败: {response.message}", []
            
    except Exception as e:
        return f"生成回答时出错：{str(e)}", []
