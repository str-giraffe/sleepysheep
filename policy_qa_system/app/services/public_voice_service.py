# 民声服务
from app.models import (
    get_public_voice_settings, update_public_voice_settings, get_public_voice_setting_changes,
    add_admin_endorsement, get_admin_endorsements, get_endorseable_topics, add_public_voice, get_public_voices
)

class PublicVoiceService:
    @staticmethod
    def get_settings():
        """获取民声设置"""
        return get_public_voice_settings()
    
    @staticmethod
    def update_settings(admin_id, min_view_count, min_like_count):
        """更新民声设置"""
        update_public_voice_settings(admin_id, min_view_count, min_like_count)
    
    @staticmethod
    def get_setting_changes(limit=20):
        """获取民声设置更改记录"""
        return get_public_voice_setting_changes(limit)
    
    @staticmethod
    def add_endorsement(topic_id, admin_id, endorsement):
        """添加管理员推举"""
        return add_admin_endorsement(topic_id, admin_id, endorsement)
    
    @staticmethod
    def get_endorsements(topic_id):
        """获取主题的管理员推举记录"""
        return get_admin_endorsements(topic_id)
    
    @staticmethod
    def get_endorseable_topics():
        """获取可推举的讨论主题"""
        return get_endorseable_topics()
    
    @staticmethod
    def add_public_voice(topic_id):
        """添加民声内容"""
        return add_public_voice(topic_id)
    
    @staticmethod
    def get_public_voices(limit=10):
        """获取民声内容"""
        return get_public_voices(limit)
