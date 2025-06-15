"""
简化的用户模型 - 单用户版本
"""
from datetime import datetime
from .database import db
import json

class User(db.Model):
    """用户表模型 - 简化版"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 固定为"single_user"
    username = db.Column(db.String(100), default="用户")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    settings = db.Column(db.Text)  # JSON格式的用户偏好设置
    
    # 关联关系
    vocabularies = db.relationship('Vocabulary', backref='user', lazy=True, cascade='all, delete-orphan')
    learning_records = db.relationship('LearningRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, user_id="single_user", username="用户", settings=None):
        self.user_id = user_id
        self.username = username
        self.settings = json.dumps(settings) if settings else json.dumps({})
    
    def get_settings(self):
        """获取用户设置"""
        if self.settings:
            return json.loads(self.settings)
        return {}
    
    def update_settings(self, new_settings):
        """更新用户设置"""
        current_settings = self.get_settings()
        current_settings.update(new_settings)
        self.settings = json.dumps(current_settings)
    
    def update_last_active(self):
        """更新最后活跃时间"""
        self.last_active = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'settings': self.get_settings()
        }
    
    @classmethod
    def get_or_create_user(cls, user_id="single_user"):
        """获取或创建用户（简化版）"""
        user = cls.query.filter_by(user_id=user_id).first()
        if not user:
            user = cls(user_id=user_id, username="用户")
            db.session.add(user)
            db.session.commit()
            print(f"创建新用户: {user_id}")
        else:
            user.update_last_active()
            db.session.commit()
        return user
    
    def __repr__(self):
        return f'<User {self.user_id}>' 