# models包初始化文件
from .database import db
from .user import User
from .vocabulary import Vocabulary
from .learning_record import LearningRecord

__all__ = ['db', 'User', 'Vocabulary', 'LearningRecord'] 