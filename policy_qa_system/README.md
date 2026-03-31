# 政策问答系统

基于 RAG 技术的智能政策咨询系统

## 系统架构

- **后端框架**: Flask
- **数据库**: SQLite
- **向量数据库**: ChromaDB
- **大语言模型**: 阿里云通义千问 (qwen-turbo)
- **嵌入模型**: 阿里云 text-embedding-v2

## 项目结构

```
policy_qa_system/
├── app/
│   ├── __init__.py
│   ├── models.py          # 数据库模型
│   ├── rag.py            # RAG 功能模块（阿里云 DashScope）
│   └── routes.py         # Flask 路由
├── templates/
│   ├── index.html        # 问答页面
│   └── admin.html        # 管理后台
├── policy.db             # SQLite 数据库（自动生成）
├── chroma.db/            # ChromaDB 向量数据库（自动生成）
├── run.py                # 应用入口
├── requirements.txt      # 依赖包
└── README.md             # 详细使用说明
```

## 安装和运行

### 1. 激活 ml 虚拟环境

```cmd
conda activate ml
```

### 2. 安装依赖

```cmd
cd f:\bishe\policy_qa_system
pip install -r requirements.txt
```

### 3. 设置阿里云 API Key

获取阿里云 DashScope API Key：
1. 访问 https://dashscope.aliyun.com/
2. 注册/登录阿里云账号
3. 在控制台获取 API Key

设置环境变量：

```cmd
set ALI_API_KEY=你的阿里云API密钥
```

或者永久设置系统环境变量。

### 4. 运行应用

```cmd
python run.py
```

### 5. 访问应用

- 问答页面: http://localhost:5000/
- 管理后台: http://localhost:5000/admin

## 使用说明

### 管理后台功能

1. **添加政策文件**
   - 填写政策标题、内容
   - 可选：来源链接、发布日期
   - 点击"添加政策"按钮

2. **构建 RAG 数据库**
   - 添加政策后，点击"构建/更新 RAG 数据库"
   - 系统会将政策内容转换为向量并存储

3. **政策管理**
   - 查看所有政策列表
   - 删除不需要的政策

### 问答页面功能

1. 输入问题
2. 点击"提问"按钮（或按 Ctrl+Enter）
3. 系统会：
   - 检索相关政策片段
   - 调用阿里云通义千问生成回答
   - 显示回答和参考内容

## 注意事项

1. 需要有效的阿里云 DashScope API Key 才能使用
2. 新用户有免费额度，具体查看阿里云官网
3. 政策数据需要先在管理后台添加
4. 添加新政策后需要重新构建 RAG 数据库
5. 政策文件内容建议使用 UTF-8 编码

## 阿里云模型说明

- **qwen-turbo**: 通义千问 Turbo 版，快速响应
- **qwen-plus**: 通义千问 Plus 版，更强的推理能力
- **qwen-max**: 通义千问 Max 版，最强性能

可在 `app/rag.py` 中修改 `LLM_MODEL` 变量切换模型。
