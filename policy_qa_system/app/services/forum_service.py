# 论坛服务
from app.models import (
    add_forum_topic, get_all_forum_topics, get_forum_topic_by_id, 
    add_forum_reply, get_forum_replies, delete_forum_topic, delete_forum_reply, like_forum_topic
)

class ForumService:
    @staticmethod
    def create_topic(user_id, title, content, has_image=0):
        """创建讨论主题"""
        return add_forum_topic(user_id, title, content, has_image)
    
    @staticmethod
    def get_all_topics():
        """获取所有讨论主题"""
        return get_all_forum_topics()
    
    @staticmethod
    def get_topic_by_id(topic_id):
        """根据ID获取讨论主题"""
        return get_forum_topic_by_id(topic_id)
    
    @staticmethod
    def create_reply(topic_id, user_id, content):
        """创建讨论回复"""
        return add_forum_reply(topic_id, user_id, content)
    
    @staticmethod
    def get_topic_replies(topic_id):
        """获取讨论主题的回复"""
        return get_forum_replies(topic_id)
    
    @staticmethod
    def delete_topic(topic_id):
        """删除讨论主题"""
        delete_forum_topic(topic_id)
    
    @staticmethod
    def delete_reply(reply_id):
        """删除讨论回复"""
        delete_forum_reply(reply_id)
    
    @staticmethod
    def like_topic(user_id, topic_id):
        """点赞讨论主题"""
        return like_forum_topic(user_id, topic_id)
