#!/usr/bin/env python3
"""
词汇收集功能测试脚本 - 单用户版本
"""
import sys
import os

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from models.database import init_db
from models.user import User
from models.vocabulary import Vocabulary
from models.learning_record import LearningRecord
from services.vocabulary_service import VocabularyService
from utils.session_manager import SessionManager
from flask import Flask

def test_vocabulary_system():
    """测试词汇系统 - 单用户版本"""
    print("=== 词汇收集系统测试（单用户版本）===")
    
    # 创建Flask应用用于测试
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_vocabulary.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'test-secret-key'
    
    with app.app_context():
        # 初始化数据库
        init_db(app)
        
        # 测试用户创建（使用固定用户ID）
        print("\n1. 测试用户创建...")
        user_id = SessionManager.get_user_id()  # 获取固定用户ID
        user = SessionManager.get_current_user()
        print(f"用户创建成功: {user.user_id} (用户名: {user.username})")
        
        # 测试词汇添加
        print("\n2. 测试词汇添加...")
        test_vocab_data = [
            {
                "word": "sophisticated",
                "pos": "adj.",
                "def_cn": "复杂的，精密的",
                "example": "This is a sophisticated system."
            },
            {
                "word": "implement",
                "pos": "v.",
                "def_cn": "实施，执行",
                "example": "We need to implement this feature."
            }
        ]
        
        result = VocabularyService.batch_add_vocabulary(
            user_id=user_id,
            vocab_list=test_vocab_data,
            source_url="http://test.com/article"
        )
        
        print(f"词汇添加结果: 成功 {result['total_added']} 个，失败 {result['total_errors']} 个")
        
        # 测试词汇查询
        print("\n3. 测试词汇查询...")
        vocabularies = VocabularyService.get_user_vocabulary(user_id)
        print(f"词汇总数: {len(vocabularies)}")
        for vocab in vocabularies:
            print(f"  - {vocab['word']}: {vocab['definition_cn']}")
        
        # 测试词汇统计
        print("\n4. 测试词汇统计...")
        stats = VocabularyService.get_vocabulary_stats(user_id)
        print(f"统计信息: {stats}")
        
        # 测试重复词汇添加
        print("\n5. 测试重复词汇添加...")
        duplicate_vocab = {
            "word": "sophisticated",
            "pos": "adj.",
            "def_cn": "高级的，老练的",
            "example": "She has sophisticated taste."
        }
        
        VocabularyService.add_vocabulary(user_id, duplicate_vocab)
        
        # 检查频率是否增加
        updated_vocab = Vocabulary.query.filter_by(
            user_id=user_id, 
            word="sophisticated"
        ).first()
        print(f"词汇 'sophisticated' 频率: {updated_vocab.frequency}")
        
        print("\n=== 测试完成 ===")
        print("✅ 单用户版本功能测试通过！")
        print(f"📚 当前用户: {user.username} ({user.user_id})")

if __name__ == "__main__":
    test_vocabulary_system() 