from flask_babel import Babel
from flask import request

babel = Babel()

def get_locale():
    # 从请求中获取语言偏好
    lang = request.args.get('lang')
    if lang in ['zh', 'en']:
        return lang
    # 从会话中获取语言
    from flask import session
    if 'lang' in session:
        return session['lang']
    # 默认语言
    return 'zh'

def init_babel(app):
    babel.init_app(app, locale_selector=get_locale)