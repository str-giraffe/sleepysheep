# complete_rag_system.py
import sqlite3
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
from datetime import datetime

class SQLiteRAGSystem:
    def __init__(self, db_file='policy_rag.db'):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 创建 policies 表（如果不存在）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_title TEXT NOT NULL,
            policy_content TEXT NOT NULL,
            category TEXT,
            source TEXT,
            publish_date TEXT,
            vector_embedding TEXT,
            content_hash TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建向量索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_policies_hash ON policies(content_hash)
        """)
        
        conn.commit()
        conn.close()
        print("✓ 数据库初始化完成")
    
    def add_policy_document(self, title, content, category=None, source=None, publish_date=None):
        """添加政策文档"""
        # 生成内容哈希（去重）
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM policies WHERE content_hash = ?", (content_hash,))
        if cursor.fetchone():
            print(f"⚠ 文档已存在: {title}")
            cursor.close()
            conn.close()
            return False
        
        # 生成简单的向量（模拟 embedding）
        # 注意：这里使用简单向量，实际应该用真正的 embedding 模型
        vector = self.simple_text_to_vector(content)
        
        # 插入数据
        cursor.execute("""
        INSERT INTO policies (policy_title, policy_content, category, source, publish_date, vector_embedding, content_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, content, category, source, publish_date, json.dumps(vector), content_hash))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ 添加政策文档: {title}")
        return True
    
    def simple_text_to_vector(self, text):
        """简单的文本向量化（模拟 embedding）"""
        # 这是一个简化的示例，实际应该使用真正的 embedding 模型
        # 这里生成一个 10 维的随机向量
        np.random.seed(hash(text) % 10000)
        vector = np.random.randn(10).tolist()
        return vector
    
    def search_similar_policies(self, query, k=3, threshold=0.5):
        """搜索相似政策"""
        # 生成查询向量
        query_vector = np.array(self.simple_text_to_vector(query))
        
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取所有政策
        cursor.execute("SELECT id, policy_title, policy_content, vector_embedding FROM policies")
        policies = cursor.fetchall()
        
        similarities = []
        for policy in policies:
            policy_vector = np.array(json.loads(policy['vector_embedding']))
            
            # 计算余弦相似度
            similarity = cosine_similarity(
                query_vector.reshape(1, -1),
                policy_vector.reshape(1, -1)
            )[0][0]
            
            if similarity >= threshold:
                similarities.append({
                    'id': policy['id'],
                    'title': policy['policy_title'],
                    'content': policy['policy_content'],
                    'similarity': float(similarity)
                })
        
        # 按相似度排序
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        cursor.close()
        conn.close()
        
        return similarities[:k]
    
    def answer_question(self, question, user_id=None, use_context=True):
        """回答问题"""
        if not use_context:
            # 不使用 RAG，直接返回简单答案
            return self.simple_answer(question)
        
        # 搜索相似政策
        similar_policies = self.search_similar_policies(question, k=3)
        
        if not similar_policies:
            return "信息库未收录相关信息"
        
        # 构建答案
        if len(similar_policies) == 1:
            best = similar_policies[0]
            answer = f"根据政策《{best['title']}》（相关度: {best['similarity']:.2%}）：\n{best['content']}"
        else:
            answer = "根据以下相关政策信息：\n"
            for i, policy in enumerate(similar_policies, 1):
                answer += f"\n{i}. 【{policy['title']}】（相关度: {policy['similarity']:.2%}）\n"
                answer += f"   {policy['content'][:100]}..." if len(policy['content']) > 100 else f"   {policy['content']}"
        
        # 记录查询
        if user_id:
            self.log_query(user_id, question, answer, 'answered', similar_policies)
        
        return answer
    
    def simple_answer(self, question):
        """简单回答（不使用 RAG）"""
        # 这里可以添加一些简单的规则匹配
        keywords_responses = {
            '税收': '根据国家税收政策，企业所得税标准税率为25%，小规模纳税人享受税收优惠。',
            '社保': '社会保险包括养老保险、医疗保险、失业保险、工伤保险和生育保险。',
            '补贴': '企业研发费用可享受加计扣除政策，高新技术企业享受15%优惠税率。',
            '人才': '各地有人才引进政策，包括住房补贴、子女教育、科研经费等支持。',
            '创业': '创业企业可享受税收减免、创业补贴、贷款贴息等优惠政策。'
        }
        
        for keyword, response in keywords_responses.items():
            if keyword in question:
                return response
        
        return "信息库未收录相关信息"
    
    def log_query(self, user_id, question, answer, status, similar_docs):
        """记录用户查询"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO user_queries (user_id, question, answer, status, similar_docs)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, question, answer, status, json.dumps(similar_docs)))
        
        # 同时记录访问日志
        cursor.execute("""
        INSERT INTO access_logs (user_id, action, resource, details)
        VALUES (?, 'query', 'policy_rag', ?)
        """, (user_id, f"提问: {question[:50]}..."))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def add_sample_policies(self):
        """添加示例政策数据"""
        sample_policies = [
            {
                'title': '高新技术企业认定管理办法',
                'content': '高新技术企业是指在《国家重点支持的高新技术领域》内，持续进行研究开发与技术成果转化，形成企业核心自主知识产权，并以此为基础开展经营活动，在中国境内（不包括港、澳、台地区）注册一年以上的居民企业。认定后三年内可享受15%的企业所得税优惠税率。',
                'category': '科技创新',
                'source': '科技部',
                'date': '2023-01-01'
            },
            {
                'title': '研发费用加计扣除政策',
                'content': '企业为开发新技术、新产品、新工艺发生的研究开发费用，未形成无形资产计入当期损益的，在按照规定据实扣除的基础上，按照研究开发费用的100%加计扣除；形成无形资产的，按照无形资产成本的200%摊销。',
                'category': '税收优惠',
                'source': '税务总局',
                'date': '2023-03-15'
            },
            {
                'title': '小微企业普惠性税收减免政策',
                'content': '对月销售额10万元以下（含本数）的增值税小规模纳税人，免征增值税。对小型微利企业年应纳税所得额不超过100万元的部分，减按25%计入应纳税所得额，按20%的税率缴纳企业所得税。',
                'category': '小微企业',
                'source': '财政部',
                'date': '2023-02-01'
            },
            {
                'title': '人才引进补贴实施办法',
                'content': '对引进的高层次人才，给予一次性安家补贴50-200万元，提供人才公寓或租房补贴，协助解决配偶就业和子女入学问题。对创业人才给予最高500万元的创业启动资金支持。',
                'category': '人才政策',
                'source': '人社部',
                'date': '2023-04-10'
            },
            {
                'title': '环境保护税收优惠政策',
                'content': '企业从事符合条件的环境保护、节能节水项目的所得，自项目取得第一笔生产经营收入所属纳税年度起，第一年至第三年免征企业所得税，第四年至第六年减半征收企业所得税。',
                'category': '环保',
                'source': '生态环境部',
                'date': '2023-05-20'
            }
        ]
        
        added = 0
        for policy in sample_policies:
            if self.add_policy_document(
                policy['title'],
                policy['content'],
                policy['category'],
                policy['source'],
                policy['date']
            ):
                added += 1
        
        print(f"\n✓ 添加了 {added} 个示例政策文档")
        return added

# 测试 RAG 系统
if __name__ == "__main__":
    rag = SQLiteRAGSystem()
    
    # 添加示例数据
    rag.add_sample_policies()
    
    # 测试搜索
    test_questions = [
        "高新技术企业有什么税收优惠？",
        "研发费用可以加计扣除吗？",
        "小微企业有哪些减免政策？",
        "人才引进有什么补贴？"
    ]
    
    print("\n" + "=" * 60)
    print("测试 RAG 系统")
    print("=" * 60)
    
    for question in test_questions:
        print(f"\n问题: {question}")
        answer = rag.answer_question(question, use_context=True)
        print(f"回答: {answer[:200]}...")