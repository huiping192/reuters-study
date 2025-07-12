"""
词汇模型
"""
from datetime import datetime
from .database import db
from sqlalchemy import UniqueConstraint

class Vocabulary(db.Model):
    """词汇表模型"""
    __tablename__ = 'vocabulary'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False, index=True)
    word = db.Column(db.String(100), nullable=False, index=True)
    pos = db.Column(db.String(20))  # 词性
    definition_cn = db.Column(db.Text)  # 中文释义
    definition_en = db.Column(db.Text)  # 英文释义
    example = db.Column(db.Text)  # 例句
    pronunciation = db.Column(db.String(100))  # 发音
    difficulty_level = db.Column(db.String(10))  # CEFR等级
    frequency = db.Column(db.Integer, default=0)  # 出现频率
    source_article_id = db.Column(db.Integer)  # 来源文章ID
    source_url = db.Column(db.Text)  # 来源URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    learning_records = db.relationship('LearningRecord', backref='vocabulary', lazy=True, cascade='all, delete-orphan')
    
    # 唯一约束：同一用户不能重复添加相同词汇
    __table_args__ = (UniqueConstraint('user_id', 'word', name='unique_user_word'),)
    
    def __init__(self, user_id, word, pos=None, definition_cn=None, definition_en=None, 
                 example=None, pronunciation=None, difficulty_level=None, 
                 source_url=None, source_article_id=None):
        self.user_id = user_id
        # 清理词汇：去除数字前缀、转换为小写并去除空格
        import re
        cleaned_word = re.sub(r'^\d+\.\s*', '', word.strip())  # 去除形如"1. "的数字前缀
        self.word = cleaned_word.lower().strip()
        self.pos = pos
        self.definition_cn = definition_cn
        self.definition_en = definition_en
        self.example = example
        self.pronunciation = pronunciation
        self.difficulty_level = difficulty_level
        self.source_url = source_url
        self.source_article_id = source_article_id
        self.frequency = 1  # 初始频率为1
    
    def increment_frequency(self):
        """增加词汇出现频率"""
        self.frequency += 1
        self.updated_at = datetime.utcnow()
    
    def update_info(self, **kwargs):
        """更新词汇信息"""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'word': self.word,
            'pos': self.pos,
            'definition_cn': self.definition_cn,
            'definition_en': self.definition_en,
            'example': self.example,
            'pronunciation': self.pronunciation,
            'difficulty_level': self.difficulty_level,
            'frequency': self.frequency,
            'source_article_id': self.source_article_id,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def add_or_update_vocabulary(cls, user_id, word_data):
        """添加或更新词汇"""
        import re
        raw_word = word_data.get('word', '')
        # 清理词汇：去除数字前缀、转换为小写并去除空格
        cleaned_word = re.sub(r'^\d+\.\s*', '', raw_word.strip())
        word = cleaned_word.lower().strip()
        if not word:
            return None
            
        # 查找是否已存在
        existing_vocab = cls.query.filter_by(user_id=user_id, word=word).first()
        
        if existing_vocab:
            # 如果已存在，增加频率并更新信息
            existing_vocab.increment_frequency()
            # 更新其他信息（如果提供了新的信息）
            update_data = {k: v for k, v in word_data.items() 
                          if k != 'word' and v is not None}
            if update_data:
                existing_vocab.update_info(**update_data)
            db.session.commit()
            return existing_vocab
        else:
            # 创建新词汇
            new_vocab = cls(user_id=user_id, **word_data)
            db.session.add(new_vocab)
            db.session.commit()
            return new_vocab
    
    @classmethod
    def get_user_vocabulary(cls, user_id, limit=None, offset=None, search=None, 
                           difficulty_level=None, sort_by='created_at', sort_order='desc'):
        """获取用户词汇列表"""
        query = cls.query.filter_by(user_id=user_id)
        
        # 搜索过滤
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    cls.word.like(search_term),
                    cls.definition_cn.like(search_term),
                    cls.definition_en.like(search_term)
                )
            )
        
        # 难度等级过滤
        if difficulty_level:
            query = query.filter_by(difficulty_level=difficulty_level)
        
        # 排序
        if sort_by == 'word':
            order_column = cls.word
        elif sort_by == 'frequency':
            order_column = cls.frequency
        elif sort_by == 'updated_at':
            order_column = cls.updated_at
        else:
            order_column = cls.created_at
            
        if sort_order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 分页
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @classmethod
    def get_vocabulary_stats(cls, user_id):
        """获取用户词汇统计"""
        total_count = cls.query.filter_by(user_id=user_id).count()
        
        # 按难度等级统计
        difficulty_stats = db.session.query(
            cls.difficulty_level, 
            db.func.count(cls.id)
        ).filter_by(user_id=user_id).group_by(cls.difficulty_level).all()
        
        # 最近7天新增词汇
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= week_ago
        ).count()
        
        return {
            'total_count': total_count,
            'recent_count': recent_count,
            'difficulty_distribution': dict(difficulty_stats)
        }
    
    def __repr__(self):
        return f'<Vocabulary {self.word} ({self.user_id})>' 