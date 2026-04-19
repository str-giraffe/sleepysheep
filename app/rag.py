import os
import requests
import json
from .models import get_all_policies

# ==================== API 配置区域 ====================
# 方式1：直接在下方填写你的 API Key（推荐用于快速测试）
# 方式2：使用环境变量（推荐用于生产环境）

# 智谱 GLM-4.7-Flash API 配置
# 请访问 https://open.bigmodel.cn/ 获取 API Key
ZHI_PU_API_KEY = "692aa27f91574b3ca055e9258a57103f.gYAsPhxzwvhUupcb"  # <-- 在这里填写你的智谱 API Key

# 腾讯混元lite API 配置
# 请访问 https://cloud.tencent.com/product/hunyuan 获取 API Key
TENCENT_API_KEY = "sk-MmLUUdpONNZ84LuJOQg57g4Qa8oExXKoDG2I3lSaTloJdQlN"  # <-- 在这里填写你的腾讯 API Key

# =====================================================

# 模型配置
LLM_MODEL = "glm-4.7-flash"  # 使用智谱 GLM-4.7-Flash
EMBEDDING_MODEL = "hunyuan-lite"  # 使用腾讯混元lite
TOP_K = 5

# 配置 API Key
if ZHI_PU_API_KEY:
    print("[OK] 已使用代码中配置的智谱 API Key")
else:
    # 尝试从环境变量读取
    try:
        ZHI_PU_API_KEY = os.environ["ZHI_PU_API_KEY"]
        print("[OK] 已使用环境变量中的智谱 API Key")
    except KeyError:
        print("[WARNING] 未能找到智谱 API Key。")
        print("   请在 app/rag.py 文件中填写 ZHI_PU_API_KEY，或设置环境变量。")
        print("   访问 https://open.bigmodel.cn/ 获取 API Key")

if TENCENT_API_KEY:
    print("[OK] 已使用代码中配置的腾讯 API Key")
else:
    # 尝试从环境变量读取
    try:
        TENCENT_API_KEY = os.environ["TENCENT_API_KEY"]
        print("[OK] 已使用环境变量中的腾讯 API Key")
    except KeyError:
        print("[WARNING] 未能找到腾讯 API Key。")
        print("   请在 app/rag.py 文件中填写 TENCENT_API_KEY，或设置环境变量。")
        print("   访问 https://cloud.tencent.com/product/hunyuan 获取 API Key")

def embed(text, is_document=True):
    """使用腾讯混元lite进行文本嵌入"""
    try:
        url = "https://hunyuan.tencentcloudapi.com"
        path = "/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TENCENT_API_KEY}"
        }
        payload = json.dumps({
            "input": [text],
            "model": "hunyuan-embedding-lite"
        })
        response = requests.post(f"{url}{path}", headers=headers, data=payload)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return result['data']['embeddings'][0]['embedding']
            else:
                raise Exception(f"嵌入失败: {result.get('message', '未知错误')}")
        else:
            raise Exception(f"嵌入失败: {response.text}")
    except Exception as e:
        raise Exception(f"嵌入过程出错: {str(e)}")

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
    # 暂时返回一个默认值，避免 ChromaDB 相关错误
    return 0

def query_rag_db(query: str):
    # 暂时返回一个空列表，避免 ChromaDB 相关错误
    return []

def generate_answer(question: str):
    try:
        find_chunks = []  # 暂时使用空列表
        
        # 构建系统提示词
        system_prompt = "你是一个政策问答助手，请根据提供的上下文准确回答用户的问题。如果上下文中没有相关信息，请说明无法回答。"
        
        # 构建用户提示词
        user_prompt = f"问题：{question}\n\n上下文：\n"
        for c in find_chunks:
            user_prompt += f"{c}\n---------\n"
        
        # 调用智谱 GLM-4.7-Flash
        url = "https://open.bigmodel.cn/api/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZHI_PU_API_KEY}"
        }
        payload = json.dumps({
            "model": "glm-4.7-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        })
        
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                answer = result['data']['choices'][0]['message']['content']
                return answer, find_chunks
            else:
                return f"生成回答失败: {result.get('message', '未知错误')}", []
        else:
            return f"生成回答失败: {response.text}", []
            
    except Exception as e:
        return f"生成回答时出错：{str(e)}", []

# 政策解读功能
def policy_interpretation(policy_id: int):
    """对指定政策进行详细解读"""
    try:
        from .models import get_policy_by_id
        policy = get_policy_by_id(policy_id)
        
        if not policy:
            return "政策未找到"
        
        # 构建系统提示词
        system_prompt = "你是一个政策解读专家，请对提供的政策进行详细解读，包括政策背景、主要内容、影响范围、实施时间等方面，语言要通俗易懂。"
        
        # 构建用户提示词
        user_prompt = f"请解读以下政策：\n\n政策标题：{policy['title']}\n政策内容：{policy['content']}"
        
        # 调用智谱 GLM-4.7-Flash
        url = "https://open.bigmodel.cn/api/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZHI_PU_API_KEY}"
        }
        payload = json.dumps({
            "model": "glm-4.7-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        })
        
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return result['data']['choices'][0]['message']['content']
            else:
                return f"解读失败: {result.get('message', '未知错误')}"
        else:
            return f"解读失败: {response.text}"
            
    except Exception as e:
        return f"解读时出错：{str(e)}"

# 政策推荐功能
def policy_recommendation(user_id: int = None, region: str = None):
    """基于用户历史或地区推荐政策"""
    try:
        policies = get_all_policies()
        
        if not policies:
            return "暂无政策可推荐"
        
        # 构建系统提示词
        system_prompt = "你是一个政策推荐专家，请根据用户的地区或历史需求，推荐最相关的政策。"
        
        # 构建用户提示词
        user_prompt = "请推荐相关政策：\n"
        if region:
            user_prompt += f"用户地区：{region}\n"
        if user_id:
            from .models import get_user_history
            history = get_user_history(user_id, limit=10)
            if history:
                user_prompt += "用户历史问题：\n"
                for item in history:
                    user_prompt += f"- {item['question']}\n"
        
        # 添加政策列表
        user_prompt += "\n可选政策：\n"
        for i, policy in enumerate(policies[:10]):  # 最多推荐10个政策
            user_prompt += f"{i+1}. {policy['title']} {policy.get('category', '')}\n"
        
        # 调用智谱 GLM-4.7-Flash
        url = "https://open.bigmodel.cn/api/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZHI_PU_API_KEY}"
        }
        payload = json.dumps({
            "model": "glm-4.7-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        })
        
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return result['data']['choices'][0]['message']['content']
            else:
                return f"推荐失败: {result.get('message', '未知错误')}"
        else:
            return f"推荐失败: {response.text}"
            
    except Exception as e:
        return f"推荐时出错：{str(e)}"

# 多轮对话功能
def multi_turn_chat(messages: list):
    """处理多轮对话"""
    try:
        # 构建系统提示词
        system_prompt = "你是一个政策问答助手，保持对话上下文，根据用户的连续提问提供准确的回答。"
        
        # 确保消息格式正确
        formatted_messages = [{'role': 'system', 'content': system_prompt}]
        
        # 添加用户和助手的消息
        for msg in messages:
            if msg['role'] in ['user', 'assistant']:
                formatted_messages.append(msg)
        
        # 调用智谱 GLM-4.7-Flash
        url = "https://open.bigmodel.cn/api/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZHI_PU_API_KEY}"
        }
        payload = json.dumps({
            "model": "glm-4.7-flash",
            "messages": formatted_messages,
            "temperature": 0.7
        })
        
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return result['data']['choices'][0]['message']['content']
            else:
                return f"对话失败: {result.get('message', '未知错误')}"
        else:
            return f"对话失败: {response.text}"
            
    except Exception as e:
        return f"对话时出错：{str(e)}"

# 政策对比功能
def policy_comparison(policy_ids: list):
    """比较多个政策之间的差异"""
    try:
        from .models import get_policy_by_id
        policies = []
        
        for policy_id in policy_ids:
            policy = get_policy_by_id(policy_id)
            if policy:
                policies.append(policy)
        
        if len(policies) < 2:
            return "至少需要两个政策进行对比"
        
        # 构建系统提示词
        system_prompt = "你是一个政策分析专家，请对比提供的政策，分析它们的异同点，包括政策目标、适用范围、实施时间、主要措施等方面。"
        
        # 构建用户提示词
        user_prompt = "请对比以下政策：\n\n"
        for i, policy in enumerate(policies):
            user_prompt += f"政策 {i+1}：{policy['title']}\n"
            user_prompt += f"内容：{policy['content'][:500]}...\n\n"
        
        # 调用智谱 GLM-4.7-Flash
        url = "https://open.bigmodel.cn/api/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZHI_PU_API_KEY}"
        }
        payload = json.dumps({
            "model": "glm-4.7-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        })
        
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return result['data']['choices'][0]['message']['content']
            else:
                return f"对比失败: {result.get('message', '未知错误')}"
        else:
            return f"对比失败: {response.text}"
            
    except Exception as e:
        return f"对比时出错：{str(e)}"
