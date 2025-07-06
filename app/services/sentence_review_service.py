"""
句子复习服务类
"""
import random
from datetime import datetime, timedelta
from models.vocabulary import Vocabulary
from models.learning_record import LearningRecord
from models.database import db
from sqlalchemy import func, and_, or_, case

class SentenceReviewService:
    """句子复习服务类"""
    
    # 复习模式定义
    REVIEW_MODES = {
        'fill_blank': '填空题',
        'choose_word': '选择词汇',
        'translate': '翻译句子',
        'context_meaning': '语境理解'
    }
    
    @staticmethod
    def get_review_words(user_id, mode='mixed', count=10, time_limit=600):
        """
        获取复习单词列表
        
        Args:
            user_id: 用户ID
            mode: 复习模式 ('fill_blank', 'choose_word', 'translate', 'context_meaning', 'mixed')
            count: 单词数量
            time_limit: 时间限制（秒）
            
        Returns:
            dict: 复习单词数据
        """
        try:
            # 获取有例句的单词，按智能算法排序
            words = SentenceReviewService._get_smart_recommendation(user_id, count)
            
            if len(words) < 4:
                return {
                    'success': False,
                    'error': '词汇库中有例句的单词数量不足，请先添加更多带例句的单词'
                }
            
            # 为每个单词生成复习模式
            review_words = []
            for word in words:
                word_data = word.to_dict()
                
                # 确定复习模式
                if mode == 'mixed':
                    word_mode = random.choice(list(SentenceReviewService.REVIEW_MODES.keys()))
                else:
                    word_mode = mode
                
                word_data['review_mode'] = word_mode
                word_data['review_mode_name'] = SentenceReviewService.REVIEW_MODES[word_mode]
                
                # 根据模式生成特定数据
                if word_mode == 'fill_blank':
                    word_data['question_data'] = SentenceReviewService._generate_fill_blank(word)
                elif word_mode == 'choose_word':
                    word_data['question_data'] = SentenceReviewService._generate_choose_word(word, words)
                elif word_mode == 'translate':
                    word_data['question_data'] = SentenceReviewService._generate_translate(word)
                elif word_mode == 'context_meaning':
                    word_data['question_data'] = SentenceReviewService._generate_context_meaning(word, words)
                
                review_words.append(word_data)
            
            return {
                'success': True,
                'data': {
                    'words': review_words,
                    'total_count': len(review_words),
                    'time_limit': time_limit,
                    'mode': mode
                }
            }
            
        except Exception as e:
            print(f"获取复习单词失败: {str(e)}")
            return {
                'success': False,
                'error': '获取复习单词失败，请稍后重试'
            }
    
    @staticmethod
    def _get_smart_recommendation(user_id, count):
        """
        智能推荐算法
        优先推荐：
        1. 有例句的单词
        2. 掌握度较低的单词
        3. 最近没有复习的单词
        4. 错误率较高的单词
        """
        # 基础查询：只选择有例句的单词
        base_query = Vocabulary.query.filter(
            and_(
                Vocabulary.user_id == user_id,
                Vocabulary.example.isnot(None),
                Vocabulary.example != ''
            )
        )
        
        # 获取单词的学习统计
        subquery = db.session.query(
            LearningRecord.vocabulary_id,
            func.avg(LearningRecord.sentence_mastery).label('avg_mastery'),
            func.count(LearningRecord.id).label('review_count'),
            func.max(LearningRecord.created_at).label('last_review'),
            func.avg(case((LearningRecord.is_correct == True, 1.0), else_=0.0)).label('accuracy')
        ).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.action_type == 'sentence_review'
        ).group_by(LearningRecord.vocabulary_id).subquery()
        
        # 连接查询
        query = base_query.outerjoin(subquery, Vocabulary.id == subquery.c.vocabulary_id)
        
        # 计算优先级分数（分数越高优先级越高）
        priority_score = (
            # 掌握度低的加分（5-掌握度）
            (5 - func.coalesce(subquery.c.avg_mastery, 0)) * 10 +
            # 复习次数少的加分
            (10 - func.coalesce(subquery.c.review_count, 0)) * 5 +
            # 最近没复习的加分
            case(
                (subquery.c.last_review.is_(None), 50),  # 从未复习
                (subquery.c.last_review < datetime.utcnow() - timedelta(days=7), 30),  # 7天未复习
                (subquery.c.last_review < datetime.utcnow() - timedelta(days=3), 20),  # 3天未复习
                (subquery.c.last_review < datetime.utcnow() - timedelta(days=1), 10),  # 1天未复习
                else_=0) +
            # 准确率低的加分
            (1 - func.coalesce(subquery.c.accuracy, 0.5)) * 20
        )
        
        # 按优先级分数排序，然后随机打散
        words = query.order_by(priority_score.desc(), func.random()).limit(count * 2).all()
        
        # 随机选择指定数量的单词
        if len(words) > count:
            words = random.sample(words, count)
        
        return words
    
    @staticmethod
    def _generate_fill_blank(word):
        """生成填空题数据"""
        if not word.example:
            return None
        
        # 将例句中的目标单词替换为空白
        example = word.example
        word_lower = word.word.lower()
        
        # 尝试不同的替换方式
        blank_sentence = example
        if word_lower in example.lower():
            # 找到单词位置并替换
            import re
            pattern = r'\b' + re.escape(word_lower) + r'\b'
            blank_sentence = re.sub(pattern, '______', example, flags=re.IGNORECASE)
        
        return {
            'sentence': blank_sentence,
            'answer': word.word,
            'original_sentence': example,
            'hint': f"({word.pos})" if word.pos else ""
        }
    
    @staticmethod
    def _generate_choose_word(word, all_words):
        """生成选择词汇题数据"""
        if not word.example:
            return None
        
        # 生成4个选项
        options = [word.word]
        other_words = [w for w in all_words if w.id != word.id]
        
        # 随机选择3个其他单词
        while len(options) < 4 and other_words:
            other_word = random.choice(other_words)
            if other_word.word not in options:
                options.append(other_word.word)
            other_words.remove(other_word)
        
        # 打乱选项顺序
        random.shuffle(options)
        
        return {
            'sentence': word.example,
            'options': options,
            'answer': word.word,
            'question': f"请选择句子中 '____' 处应该填入的单词："
        }
    
    @staticmethod
    def _generate_translate(word):
        """生成翻译题数据"""
        if not word.example:
            return None
        
        return {
            'sentence': word.example,
            'answer': word.definition_cn,
            'word': word.word,
            'question': "请翻译以下包含目标单词的句子："
        }
    
    @staticmethod
    def _generate_context_meaning(word, all_words):
        """生成语境理解题数据"""
        if not word.example or not word.definition_cn:
            return None
        
        # 生成4个释义选项
        options = [word.definition_cn]
        other_words = [w for w in all_words if w.id != word.id and w.definition_cn]
        
        # 随机选择3个其他单词的释义
        while len(options) < 4 and other_words:
            other_word = random.choice(other_words)
            if other_word.definition_cn not in options:
                options.append(other_word.definition_cn)
            other_words.remove(other_word)
        
        # 打乱选项顺序
        random.shuffle(options)
        
        return {
            'sentence': word.example,
            'word': word.word,
            'options': options,
            'answer': word.definition_cn,
            'question': f"在以下句子中，单词 '{word.word}' 的含义是："
        }
    
    @staticmethod
    def record_sentence_review(user_id, vocabulary_id, context_type, is_correct, 
                             response_time=None, sentence_mastery=None):
        """记录句子复习结果"""
        try:
            # 如果没有提供句子掌握度，根据正确性计算
            if sentence_mastery is None:
                sentence_mastery = 3 if is_correct else 1
            
            # 记录学习行为
            record = LearningRecord(
                user_id=user_id,
                vocabulary_id=vocabulary_id,
                action_type='sentence_review',
                is_correct=is_correct,
                response_time=response_time,
                sentence_mastery=sentence_mastery,
                context_type=context_type
            )
            
            db.session.add(record)
            db.session.commit()
            
            return record.to_dict()
            
        except Exception as e:
            print(f"记录句子复习失败: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_sentence_review_stats(user_id):
        """获取句子复习统计"""
        try:
            # 获取基本统计
            stats = LearningRecord.get_sentence_review_stats(user_id)
            
            # 获取最近复习的单词
            recent_reviews = db.session.query(
                Vocabulary.word,
                LearningRecord.context_type,
                LearningRecord.is_correct,
                LearningRecord.sentence_mastery,
                LearningRecord.created_at
            ).join(
                LearningRecord, Vocabulary.id == LearningRecord.vocabulary_id
            ).filter(
                LearningRecord.user_id == user_id,
                LearningRecord.action_type == 'sentence_review'
            ).order_by(
                LearningRecord.created_at.desc()
            ).limit(10).all()
            
            stats['recent_reviews'] = [
                {
                    'word': review.word,
                    'context_type': review.context_type,
                    'is_correct': review.is_correct,
                    'sentence_mastery': review.sentence_mastery,
                    'created_at': review.created_at.isoformat()
                }
                for review in recent_reviews
            ]
            
            return stats
            
        except Exception as e:
            print(f"获取句子复习统计失败: {str(e)}")
            return None