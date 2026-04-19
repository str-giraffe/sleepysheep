# 政策问答系统

基于 RAG 技术的智能政策咨询系统

## 系统架构

- **后端框架**: Flask
- **数据库**: SQLite
- **向量数据库**: ChromaDB
- **大语言模型**: 智谱 GLM-4.7-Flash
- **嵌入模型**: 腾讯混元 lite
- **服务层架构**: 模块化业务逻辑分离

## 项目结构

```
policy_qa_system/
├── app/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── models.py          # 数据库模型
│   ├── rag.py            # RAG 功能模块
│   ├── routes.py         # Flask 路由
│   └── services/         # 服务层
│       ├── __init__.py
│       ├── user_service.py
│       ├── policy_service.py
│       ├── forum_service.py
│       ├── user_history_service.py
│       ├── expert_service.py
│       ├── public_voice_service.py
│       └── statistics_service.py
├── templates/
│   ├── index.html        # 问答页面
│   ├── admin_index.html  # 管理后台首页
│   ├── admin_policies.html  # 政策管理
│   ├── admin_categories.html  # 分类管理
│   ├── admin_tags.html   # 标签管理
│   ├── admin_users.html  # 用户管理
│   ├── admin_experts.html  # 专家管理
│   ├── admin_interpretations.html  # 解读管理
│   ├── admin_public_voice.html  # 民声管理
│   ├── admin_statistics.html  # 数据统计
│   ├── admin_rag.html    # RAG管理
│   ├── forum.html        # 讨论广场
│   ├── forum_topic.html  # 讨论主题详情
│   ├── public_voice_detail.html  # 民声详情
│   ├── policy_detail.html  # 政策详情
│   ├── interpretation_detail.html  # 解读详情
│   ├── search.html       # 搜索页面
│   ├── login.html        # 登录页面
│   └── profile.html      # 用户个人中心
├── css/
│   └── main.css          # 主样式文件
├── policy.db             # SQLite 数据库（自动生成）
├── chroma.db/            # ChromaDB 向量数据库（自动生成）
├── run.py                # 应用入口
├── requirements.txt      # 依赖包
├── README.md             # 详细使用说明
└── spider_real.py        # 政策数据爬取脚本
```

## 安装和运行

### 1. 激活虚拟环境

```cmd
# 创建并激活虚拟环境
python -m venv venv
venv\Scripts\activate
```

### 2. 安装依赖

```cmd
cd f:\bishe\policy_qa_system
pip install -r requirements.txt
```

### 3. 设置 API Key

#### 3.1 智谱 API Key

获取智谱 API Key：
1. 访问 https://open.bigmodel.cn/
2. 注册/登录账号
3. 在控制台获取 API Key

#### 3.2 腾讯混元 API Key

获取腾讯混元 API Key：
1. 访问 https://cloud.tencent.com/product/hunyuan
2. 注册/登录账号
3. 在控制台获取 API Key

#### 3.3 设置环境变量

```cmd
set ZHIPU_API_KEY=你的智谱API密钥
set TENCENT_API_KEY=你的腾讯API密钥
```

或者在 `app/rag.py` 文件中直接设置：

```python
# 智谱 API Key
ZHIPU_API_KEY = "你的智谱API密钥"

# 腾讯混元 API Key
TENCENT_API_KEY = "你的腾讯API密钥"
```

### 4. 运行应用

```cmd
python run.py
```

### 5. 访问应用

- 问答页面: http://localhost:5000/
- 管理后台: http://localhost:5000/admin
- 讨论广场: http://localhost:5000/forum
- 个人中心: http://localhost:5000/profile
- 搜索页面: http://localhost:5000/search

## 核心功能

### 1. 智能政策问答
- 基于 RAG 技术的智能问答
- 支持多轮对话
- 政策解读和推荐
- 政策对比分析

### 2. 管理后台
- **政策管理**: 添加、删除政策，支持按分类和时间查询
- **分类管理**: 管理政策分类
- **标签管理**: 管理政策标签
- **用户管理**: 角色管理，用户封禁
- **专家管理**: 专家认证审核
- **解读管理**: 专家解读审核
- **民声管理**: 民声设置和推举管理
- **数据统计**: 系统数据概览
- **RAG管理**: 构建和更新 RAG 数据库

### 3. 讨论广场
- 发布讨论主题
- 回复和点赞
- 实时更新功能
- 民声推举机制

### 4. 个人中心
- 查看问答历史
- 管理收藏政策
- 专家认证申请
- 个人信息管理

### 5. 数据爬取
- 支持从政府网站爬取真实政策数据
- 覆盖教育、医疗、就业、住房、社保、税收、创业、其他等领域
- 数据自动去重和分类

## 技术特点

### 1. 后端优化
- **服务层架构**: 模块化业务逻辑分离
- **配置管理**: 统一的配置系统
- **性能优化**: 缓存支持和查询优化
- **安全性**: 密码验证和输入验证
- **可维护性**: 清晰的代码结构

### 2. 前端体验
- **响应式设计**: 适配不同设备
- **实时更新**: 讨论广场实时刷新
- **交互友好**: 流畅的用户界面
- **视觉设计**: 红金橙配色方案，庄重严肃的氛围

### 3. 智能功能
- **RAG 技术**: 检索增强生成
- **向量数据库**: 高效的相似性搜索
- **多模型集成**: 智谱 GLM-4.7-Flash + 腾讯混元
- **上下文理解**: 多轮对话支持

## 数据来源

- **真实数据**: 从政府网站爬取的政策文件
- **覆盖领域**: 教育、医疗、就业、住房、社保、税收、创业、其他
- **数据量**: 5000+ 条政策数据
- **更新机制**: 支持定期爬取更新

## 注意事项

1. 需要有效的智谱和腾讯 API Key 才能使用
2. 新用户有免费额度，具体查看各平台官网
3. 首次运行需要构建 RAG 数据库
4. 爬取数据时需要注意网络环境和反爬措施
5. 建议使用 Python 3.8+ 版本

## 模型说明

### 智谱 GLM-4.7-Flash
- **特点**: 快速响应，适合实时对话
- **应用**: 政策问答、对话生成

### 腾讯混元 lite
- **特点**: 高效的文本嵌入，适合向量检索
- **应用**: 政策文本向量化、相似性搜索

## 扩展建议

1. **添加更多数据源**: 整合更多政府网站和政策数据库
2. **优化 RAG 算法**: 改进检索策略和上下文融合
3. **增加多语言支持**: 支持中英文政策问答
4. **部署到云平台**: 提高系统稳定性和可扩展性
5. **添加用户反馈机制**: 持续优化系统性能
