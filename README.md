 一、实践周完成内容说明
1. 毕设推进
本次实践周主要推进了政务政策问答系统的设计与开发工作。该系统基于RAG（检索增强生成）技术，实现了智能化的政策咨询服务。完成了以下核心功能：
智能问答模块：集成智谱GLM-4大语言模型，实现政策问题的智能回答，支持多轮对话上下文理解
政策管理模块：完成政策的增删改查、分类管理、标签管理等功能
专家解读模块：专家用户可以发布政策解读内容，供普通用户参考
讨论广场模块：支持用户发布讨论主题、回复互动、收藏等功能
管理后台模块：提供完整的系统管理功能，包括用户管理、政策管理、数据统计等
 2. 专业学习
在项目开发过程中，深入学习了以下专业知识：
RAG技术原理：掌握了检索增强生成技术的核心思想，了解了向量检索与语言模型生成的结合方式
向量数据库技术：学习了ChromaDB的使用，理解了文本向量化的原理和应用场景
Flask Web开发：深入学习了Flask框架的路由系统、模板引擎、蓝图机制等
服务层架构设计：实践了模块化的服务层架构模式，提高了代码的可维护性
 二、详细过程说明：RAG智能问答功能的实现
1. 技术选型
在智能问答功能的技术选型上，选择了以下方案：
后端框架：Flask 2.0+，轻量级Web框架，便于快速开发
向量数据库：ChromaDB 0.4+，支持高效的向量存储和相似度检索
嵌入模型：腾讯混元嵌入模型，将政策文本转换为向量表示
大语言模型：智谱GLM-4.7-Flash，用于生成自然语言回答
2. 实现过程
第一步：政策文档向量化处理
首先需要将政策文档转换为向量形式存储到ChromaDB中。具体步骤包括：
1. 读取政策文档内容，进行文本预处理（去除HTML标签、特殊字符等）
2. 将长文本切分为合适的块（Chunk），每块包含完整的语义信息
3. 调用腾讯混元嵌入API，将文本块转换为向量
4. 将向量及其元数据存储到ChromaDB集合中
```python
def process_policy_document(policy_id, content):
    # 文本分块
    chunks = text_chunking(content, chunk_size=500)
    # 向量化并存储
    for chunk in chunks:
        vector = embedding_model.embed(chunk)
        collection.add(
            embeddings=[vector],
            documents=[chunk],
            metadatas=[{"policy_id": policy_id}]
        )
```
第二步：用户查询处理
当用户提出问题时，系统需要进行以下处理：
1. 接收用户查询文本
2. 使用相同的嵌入模型将查询转换为向量
3. 在ChromaDB中进行相似度检索，获取最相关的政策文档块
4. 对检索结果进行重排序，提高准确性
第三步：答案生成
将检索到的政策文档作为上下文，结合用户的查询构建Prompt，发送给智谱GLM-4模型生成回答。回答中会包含参考来源的引用，方便用户追溯政策依据。
3. 核心代码实现
```python
class RAGEngine:
    def __init__(self, embedding_model, chroma_collection, llm_client):
        self.embedder = embedding_model
        self.collection = chroma_collection
        self.llm = llm_client
    
    def retrieve(self, query, top_k=5):
        query_vec = self.embedder.embed(query)
        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=["metadatas", "documents"]
        )
        return results['documents'][0], results['metadatas'][0]
    
    def generate_answer(self, query, contexts):
        context_str = "\n\n".join([f"[{i+1}]{doc}" for i, doc in enumerate(contexts)])
        prompt = PROMPT_TEMPLATE.format(context_str=context_str, question=query)
        response = self.llm.chat_completions.create(
            model="glm-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content
```
 三、遇到的问题及解决方法
问题一：侧边栏交互功能不一致
问题描述：系统在不同页面的侧边栏交互行为不统一，有的页面侧边栏无法正常弹出和收回。
原因分析：不同页面使用了不同的JavaScript代码实现侧边栏功能，缺乏统一的实现标准。
解决方法：编写了统一的侧边栏交互代码，包括：点击按钮切换显示/隐藏、鼠标悬停自动显示/隐藏、点击其他区域自动关闭、ESC键快速关闭等功能。将该代码统一添加到所有页面模板中。
问题二：用户认证功能异常
问题描述：登录页面提交表单时提示"Method Not Allowed"错误。
原因分析：登录路由只支持GET方法，没有处理POST请求。
解决方法：修改登录路由，添加`methods=['GET', 'POST']`参数，同时在POST处理逻辑中调用`UserService.verify_user()`方法验证用户凭据，成功后创建会话并重定向到首页。
四、实践总结
  本次实践周的学习和工作经历让我收获颇丰。作为一名计算机科学与技术专业的学生，我深刻认识到理论知识与实践能力相结合的重要性。
  在毕设推进方面，我通过政务政策问答系统的开发，将课堂所学的Web开发知识与前沿的AI技术相结合。RAG技术的学习让我理解了如何将大规模语言模型与垂直领域的知识库相结合，提高回答的准确性和可信度。这个过程中，我不仅掌握了ChromaDB向量数据库的使用方法，还深入了解了文本向量化的原理，这对我的专业视野是一次很大的拓展。
  在项目开发过程中，我也遇到了一些技术难题。比如最初设计的侧边栏交互功能在各个页面表现不一致，这让我意识到在团队协作或大型项目中统一编码规范的重要性。于是我花了额外的时间去统一各页面的交互逻辑，这个经历让我明白了软件工程中"高内聚低耦合"原则的实际价值。
  性能优化方面的学习也让我印象深刻。当我最初设定的性能指标在测试中无法达到时，我学会了如何客观地分析问题根源，而不是盲目追求不切实际的目标。通过查阅资料和实际测试，我了解到Flask开发服务器与生产级服务器的性能差异，这对我未来进行系统架构设计提供了宝贵的经验。
  这次实践周不仅让我完成了毕设项目的关键功能开发，更重要的是让我在解决问题的过程中提升了工程实践能力。我深刻体会到，一个合格的软件工程师不仅需要扎实的技术基础，更需要严谨的工作态度和持续学习的能力。未来的学习和工作中，我将继续保持这种实践精神，努力提升自己的专业素养。
