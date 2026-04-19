# 数据统计服务
from app.models import get_statistics

class StatisticsService:
    @staticmethod
    def get_statistics():
        """获取系统统计数据"""
        return get_statistics()
