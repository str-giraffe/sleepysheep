# digital_human_simple.py
"""
简易数字人系统 - 不需要复杂依赖
集成到现有的 Flask 政策解读系统
"""

import os
import json
from datetime import datetime
import subprocess
import threading
import tempfile
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# 检查是否有简单TTS功能
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠ pyttsx3 未安装，将使用文本显示")

# 检查是否有音频播放功能
try:
    import simpleaudio as sa
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠ simpleaudio 未安装，将无法播放音频")

class SimpleDigitalHuman:
    """简易数字人类"""
    
    def __init__(self, app):
        self.app = app
        self.setup_routes()
        
        # 数字人配置
        self.config = {
            'avatar_images': {
                'idle': 'static/avatar_idle.png',
                'talking': 'static/avatar_talking.png',
                'thinking': 'static/avatar_thinking.png'
            },
            'voice_speed': 150,  # 语速
            'voice_volume': 0.9,  # 音量
        }
        
        # 初始化TTS引擎
        self.tts_engine = None
        if TTS_AVAILABLE:
            self.init_tts()
    
    def init_tts(self):
        """初始化TTS引擎"""
        try:
            self.tts_engine = pyttsx3.init()
            # 设置语速
            self.tts_engine.setProperty('rate', self.config['voice_speed'])
            # 设置音量
            self.tts_engine.setProperty('volume', self.config['voice_volume'])
            # 设置声音（如果有中文语音）
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"⚠ TTS初始化失败: {e}")
    
    def speak_text(self, text):
        """文本转语音"""
        if not TTS_AVAILABLE or not self.tts_engine:
            return None
        
        try:
            # 保存为临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                temp_file = tmp.name
            
            # 保存语音到文件
            self.tts_engine.save_to_file(text, temp_file)
            self.tts_engine.runAndWait()
            
            return temp_file
        except Exception as e:
            print(f"⚠ 语音合成失败: {e}")
            return None
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.route('/digital_human')
        def digital_human_page():
            """数字人主页面"""
            if 'username' not in session:
                return redirect(url_for('login'))
            return render_template('digital_human.html')
        
        @self.app.route('/api/digital_human/speak', methods=['POST'])
        def digital_human_speak():
            """数字人说话"""
            if 'username' not in session:
                return jsonify({'error': '未登录'}), 401
            
            data = request.get_json()
            text = data.get('text', '')
            
            if not text:
                return jsonify({'error': '文本不能为空'}), 400
            
            # 生成语音文件
            audio_file = self.speak_text(text)
            
            if audio_file and os.path.exists(audio_file):
                # 转换为base64或返回文件路径
                return jsonify({
                    'success': True,
                    'text': text,
                    'audio_url': f'/static/temp/{os.path.basename(audio_file)}',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': True,
                    'text': text,
                    'message': '语音生成失败，使用文本显示',
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.app.route('/api/digital_human/animate', methods=['POST'])
        def digital_human_animate():
            """触发数字人动画"""
            data = request.get_json()
            animation = data.get('animation', 'idle')
            
            animations = {
                'idle': {'state': 'idle', 'duration': 0},
                'talking': {'state': 'talking', 'duration': 2000},
                'thinking': {'state': 'thinking', 'duration': 1000},
                'nod': {'state': 'nod', 'duration': 500},
                'shake': {'state': 'shake', 'duration': 500}
            }
            
            return jsonify({
                'success': True,
                'animation': animations.get(animation, animations['idle'])
            })

# 在现有的 Flask 应用中集成
def create_app():
    app = Flask(__name__)
    app.secret_key = 'digital-human-policy-system'
    
    # 创建数字人实例
    digital_human = SimpleDigitalHuman(app)
    
    return app, digital_human