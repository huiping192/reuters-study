"""
词汇管理服务
"""
from models.vocabulary import Vocabulary
from models.learning_record import LearningRecord
from models.database import db

class VocabularyService:
    """词汇管理服务类"""
    
    @staticmethod
    def add_vocabulary(user_id, vocab_data):
        """添加词汇到用户词汇库"""
        try:
            # 数据验证
            if not vocab_data.get('word'):
                raise ValueError("词汇不能为空")
            
            # 处理词汇数据
            processed_data = {
                'word': vocab_data.get('word', '').strip(),
                'pos': vocab_data.get('pos', ''),
                'definition_cn': vocab_data.get('def_cn', ''),
                'definition_en': vocab_data.get('definition_en', ''),
                'example': vocab_data.get('example', ''),
                'pronunciation': vocab_data.get('pronunciation', ''),
                'difficulty_level': vocab_data.get('difficulty_level', ''),
                'source_url': vocab_data.get('source_url', ''),
                'source_article_id': vocab_data.get('source_article_id')
            }
            
            # 添加或更新词汇
            vocabulary = Vocabulary.add_or_update_vocabulary(user_id, processed_data)
            
            if vocabulary:
                # 记录学习行为
                LearningRecord.record_action(
                    user_id=user_id,
                    vocabulary_id=vocabulary.id,
                    action_type='view'
                )
                
                print(f"词汇已保存: {vocabulary.word} (用户: {user_id})")
                return vocabulary
            
            return None
            
        except Exception as e:
            print(f"添加词汇失败: {str(e)}")
            db.session.rollback()
            raise e
    
    @staticmethod
    def batch_add_vocabulary(user_id, vocab_list, source_url=None):
        """批量添加词汇"""
        added_vocabularies = []
        errors = []
        
        for vocab_data in vocab_list:
            try:
                # 添加来源信息
                if source_url:
                    vocab_data['source_url'] = source_url
                
                vocabulary = VocabularyService.add_vocabulary(user_id, vocab_data)
                if vocabulary:
                    added_vocabularies.append(vocabulary)
                    
            except Exception as e:
                errors.append({
                    'word': vocab_data.get('word', 'unknown'),
                    'error': str(e)
                })
        
        return {
            'added': added_vocabularies,
            'errors': errors,
            'total_added': len(added_vocabularies),
            'total_errors': len(errors)
        }
    
    @staticmethod
    def get_user_vocabulary(user_id, filters=None):
        """获取用户词汇列表"""
        if not filters:
            filters = {}
        
        vocabularies = Vocabulary.get_user_vocabulary(
            user_id=user_id,
            limit=filters.get('limit'),
            offset=filters.get('offset'),
            search=filters.get('search'),
            difficulty_level=filters.get('difficulty_level'),
            sort_by=filters.get('sort_by', 'created_at'),
            sort_order=filters.get('sort_order', 'desc')
        )
        
        return [vocab.to_dict() for vocab in vocabularies]
    
    @staticmethod
    def update_vocabulary(vocab_id, updates):
        """更新词汇信息"""
        try:
            vocabulary = Vocabulary.query.get(vocab_id)
            if not vocabulary:
                raise ValueError("词汇不存在")
            
            vocabulary.update_info(**updates)
            db.session.commit()
            
            return vocabulary.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def delete_vocabulary(vocab_id):
        """删除词汇"""
        try:
            vocabulary = Vocabulary.query.get(vocab_id)
            if not vocabulary:
                raise ValueError("词汇不存在")
            
            db.session.delete(vocabulary)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def search_vocabulary(user_id, query):
        """搜索词汇"""
        vocabularies = Vocabulary.get_user_vocabulary(
            user_id=user_id,
            search=query,
            limit=50  # 限制搜索结果数量
        )
        
        return [vocab.to_dict() for vocab in vocabularies]
    
    @staticmethod
    def get_vocabulary_stats(user_id):
        """获取词汇统计信息"""
        return Vocabulary.get_vocabulary_stats(user_id)
    
    @staticmethod
    def get_vocabulary_detail(vocab_id, user_id):
        """获取词汇详情"""
        vocabulary = Vocabulary.query.filter_by(id=vocab_id, user_id=user_id).first()
        if not vocabulary:
            return None
        
        # 获取学习记录
        learning_history = LearningRecord.get_learning_history(
            user_id=user_id,
            vocabulary_id=vocab_id,
            limit=10
        )
        
        vocab_dict = vocabulary.to_dict()
        vocab_dict['learning_history'] = [record.to_dict() for record in learning_history]
        
        return vocab_dict
    
    @staticmethod
    def mark_vocabulary_mastery(user_id, vocab_id, mastery_level):
        """标记词汇掌握程度"""
        try:
            # 记录掌握程度
            LearningRecord.record_action(
                user_id=user_id,
                vocabulary_id=vocab_id,
                action_type='master',
                mastery_level=mastery_level
            )
            
            return True
            
        except Exception as e:
            print(f"标记掌握程度失败: {str(e)}")
            return False
    
    @staticmethod
    def get_vocabulary_count(user_id, filters=None):
        """获取词汇总数"""
        if not filters:
            filters = {}
        
        query = Vocabulary.query.filter_by(user_id=user_id)
        
        # 搜索过滤
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                db.or_(
                    Vocabulary.word.like(search_term),
                    Vocabulary.definition_cn.like(search_term),
                    Vocabulary.definition_en.like(search_term)
                )
            )
        
        # 难度等级过滤
        if filters.get('difficulty_level'):
            query = query.filter_by(difficulty_level=filters['difficulty_level'])
        
        return query.count() 