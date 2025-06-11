"""
学习记录模型
"""
from datetime import datetime
from .database import db

class LearningRecord(db.Model):
    """学习记录表模型"""
    __tablename__ = 'learning_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False, index=True)
    vocabulary_id = db.Column(db.Integer, db.ForeignKey('vocabulary.id'), nullable=False, index=True)
    action_type = db.Column(db.String(20), nullable=False)  # 'view', 'review', 'test', 'master'
    mastery_level = db.Column(db.Integer, default=0)  # 掌握程度 0-5
    response_time = db.Column(db.Integer)  # 响应时间(毫秒)
    is_correct = db.Column(db.Boolean)  # 是否正确(测试时)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __init__(self, user_id, vocabulary_id, action_type, mastery_level=0, 
                 response_time=None, is_correct=None):
        self.user_id = user_id
        self.vocabulary_id = vocabulary_id
        self.action_type = action_type
        self.mastery_level = mastery_level
        self.response_time = response_time
        self.is_correct = is_correct
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vocabulary_id': self.vocabulary_id,
            'action_type': self.action_type,
            'mastery_level': self.mastery_level,
            'response_time': self.response_time,
            'is_correct': self.is_correct,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def record_action(cls, user_id, vocabulary_id, action_type, **kwargs):
        """记录学习行为"""
        record = cls(
            user_id=user_id,
            vocabulary_id=vocabulary_id,
            action_type=action_type,
            **kwargs
        )
        db.session.add(record)
        db.session.commit()
        return record
    
    @classmethod
    def get_learning_history(cls, user_id, vocabulary_id=None, limit=None):
        """获取学习历史"""
        query = cls.query.filter_by(user_id=user_id)
        
        if vocabulary_id:
            query = query.filter_by(vocabulary_id=vocabulary_id)
        
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @classmethod
    def get_learning_stats(cls, user_id, period_days=7):
        """获取学习统计"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # 总学习次数
        total_actions = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= start_date
        ).count()
        
        # 按行为类型统计
        action_stats = db.session.query(
            cls.action_type,
            db.func.count(cls.id)
        ).filter(
            cls.user_id == user_id,
            cls.created_at >= start_date
        ).group_by(cls.action_type).all()
        
        # 每日学习统计
        daily_stats = db.session.query(
            db.func.date(cls.created_at).label('date'),
            db.func.count(cls.id).label('count')
        ).filter(
            cls.user_id == user_id,
            cls.created_at >= start_date
        ).group_by(db.func.date(cls.created_at)).all()
        
        return {
            'total_actions': total_actions,
            'action_distribution': dict(action_stats),
            'daily_stats': [{'date': str(date), 'count': count} for date, count in daily_stats]
        }
    
    def __repr__(self):
        return f'<LearningRecord {self.action_type} - {self.user_id}>' 