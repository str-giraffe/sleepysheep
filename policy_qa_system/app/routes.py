from flask import Flask, render_template, request, jsonify
from .models import init_db, add_policy, get_all_policies, get_policy_by_id, delete_policy
from .rag import create_rag_db, generate_answer
import os

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/policies', methods=['GET'])
def api_get_policies():
    policies = get_all_policies()
    return jsonify(policies)

@app.route('/api/policies', methods=['POST'])
def api_add_policy():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    source_url = data.get('source_url')
    publish_date = data.get('publish_date')
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    policy_id = add_policy(title, content, source_url, publish_date)
    return jsonify({'id': policy_id, 'message': '政策添加成功'})

@app.route('/api/policies/<int:policy_id>', methods=['GET'])
def api_get_policy(policy_id):
    policy = get_policy_by_id(policy_id)
    if policy:
        return jsonify(policy)
    return jsonify({'error': '政策未找到'}), 404

@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
def api_delete_policy(policy_id):
    delete_policy(policy_id)
    return jsonify({'message': '政策删除成功'})

@app.route('/api/rag/build', methods=['POST'])
def api_build_rag():
    try:
        count = create_rag_db()
        return jsonify({'message': f'RAG 数据库构建成功，共处理 {count} 个文本片段'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/qa', methods=['POST'])
def api_qa():
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    answer, chunks = generate_answer(question)
    return jsonify({'answer': answer, 'chunks': chunks})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
