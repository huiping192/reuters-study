import requests
from flask import Flask, render_template
from flask import request, jsonify
from flask_migrate import Migrate

from audio_manager import generate_audio
from news_analytics import ArticleProcessor
from reuters_manager import get_reuters_news_with_subcategory, get_reuters_article, split_into_paragraphs
import urllib.parse
from flask import send_from_directory
import os

# 导入新增的模块
from models.database import init_db, db
from utils.session_manager import SessionManager
from services.vocabulary_service import VocabularyService
from models.learning_record import LearningRecord

app = Flask(__name__)

# 配置session（简化版）
SessionManager.set_session_config(app)

# 首先配置数据库连接但不创建表
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data/vocabulary.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 初始化 Flask-Migrate
migrate = Migrate(app, db)

# 然后初始化数据库（包括自动migration）
init_db(app)

# 配置音频存储路径
TTS_DIR = os.path.join(app.static_folder, 'tts')
os.makedirs(TTS_DIR, exist_ok=True)


@app.route('/')
def index():
    # 获取新闻数据
    news_data = get_reuters_news_with_subcategory()

    # 如果获取失败显示错误信息
    if not news_data:
        return render_template('error.html', message="Failed to fetch news")

    # 转换为普通字典便于模板处理
    processed_data = {
        main_cat: dict(sub_cats)
        for main_cat, sub_cats in news_data.items()
    }

    return render_template('list.html', news=processed_data)


# 详情页路由（保持之前的实现）
@app.route('/news/<path:encoded_url>')
def detail(encoded_url):
    try:
        # 解码URL并获取文章内容
        news_url = urllib.parse.unquote(encoded_url)
        article = get_reuters_article(news_url)
        # 解析内容段落
        paragraphs = split_into_paragraphs(article['content'])
        # 构造上下文数据
        article_data = {
            "title": article['title'],
            "url": news_url,
            "paragraphs": paragraphs,
            "original_content": article['content'],  # 保留原始内容备用
            "publish_date": article.get('date', '')  # 假设有日期字段
        }

        return render_template('detail.html', article=article_data)

    except requests.exceptions.RequestException as e:
        return render_template('error.html',
                               message=f"Failed to fetch article: {str(e)}"), 500
    except KeyError as e:
        return render_template('error.html',
                               message=f"Article format error: {str(e)}"), 500
    except Exception as e:
        return render_template('error.html',
                               message=f"Unexpected error: {str(e)}"), 500


@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    try:
        if not data or 'text' not in data:
            return jsonify({'error': 'Invalid request format'}), 400

        # 验证文本内容
        input_text = data['text'].strip()
        if not input_text:
            return jsonify({'error': 'Empty text content'}), 400

        # 获取固定用户ID
        user_id = SessionManager.get_user_id()
        
        # 获取来源URL（如果有的话）
        source_url = data.get('source_url')

        processor = ArticleProcessor()
        # 传递用户ID和来源URL以启用词汇收集
        translated_objc = processor.process_article(
            input_text, 
            user_id=user_id,
            source_url=source_url
        )

        # 验证返回结果
        if not translated_objc:
            raise ValueError("Invalid translation result")

        print(translated_objc)
        # 渲染模板并返回HTML
        html = render_template('translation_template.html', 
                              vocabulary=translated_objc['vocabulary'],
                              translation=translated_objc['translation'])

        return jsonify({
            'index': data.get('index', -1),
            'translation': translated_objc,
            'html': html
        })

    except Exception as e:
        print(f"Translation Error: {str(e)}")
        return jsonify({
            'error': str(e),
            'index': data.get('index', -1)
        }), 500


@app.route('/tts', methods=['POST'])
def handle_tts():
    data = request.json
    try:
        filename = generate_audio(data['text'], TTS_DIR)
        return jsonify({
            'success': True,
            'audio_url': f'/tts/{filename}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/tts/<filename>')
def serve_audio(filename):
    return send_from_directory(TTS_DIR, filename)


# 词汇相关API端点
@app.route('/api/vocabulary', methods=['GET', 'POST'])
def vocabulary_api():
    """词汇API端点"""
    try:
        user_id = SessionManager.get_user_id()
        
        if request.method == 'GET':
            # 获取查询参数
            filters = {
                'limit': request.args.get('limit', type=int),
                'offset': request.args.get('offset', type=int),
                'search': request.args.get('search'),
                'difficulty_level': request.args.get('difficulty_level'),
                'sort_by': request.args.get('sort_by', 'created_at'),
                'sort_order': request.args.get('sort_order', 'desc')
            }
            
            # 计算分页
            page = request.args.get('page', 1, type=int)
            limit = filters['limit'] or 20
            offset = (page - 1) * limit
            filters['limit'] = limit
            filters['offset'] = offset
            
            vocabularies = VocabularyService.get_user_vocabulary(user_id, filters)
            total = VocabularyService.get_vocabulary_count(user_id, filters)
            
            return jsonify({
                'success': True,
                'data': vocabularies,
                'total': total,
                'page': page,
                'limit': limit
            })
            
        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'word' not in data:
                return jsonify({
                    'success': False,
                    'error': '缺少必要参数'
                }), 400
                
            # 添加词汇
            result = VocabularyService.add_vocabulary(user_id, {
                'word': data['word'],
                'source_url': data.get('source_url')
            })
            
            # 将Vocabulary对象转换为字典
            if result:
                result_dict = {
                    'id': result.id,
                    'word': result.word,
                    'definition_cn': result.definition_cn,
                    'definition_en': result.definition_en,
                    'pos': result.pos,
                    'example': result.example,
                    'difficulty_level': result.difficulty_level,
                    'source_url': result.source_url,
                    'created_at': result.created_at.isoformat() if result.created_at else None,
                    'updated_at': result.updated_at.isoformat() if result.updated_at else None
                }
            else:
                result_dict = None
            
            return jsonify({
                'success': True,
                'data': result_dict
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/vocabulary/stats', methods=['GET'])
def get_vocabulary_stats():
    """获取词汇统计信息"""
    try:
        user_id = SessionManager.get_user_id()
        stats = VocabularyService.get_vocabulary_stats(user_id)
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/vocabulary/<int:vocab_id>', methods=['GET'])
def get_vocabulary_detail(vocab_id):
    """获取词汇详情"""
    try:
        user_id = SessionManager.get_user_id()
        vocab_detail = VocabularyService.get_vocabulary_detail(vocab_id, user_id)
        
        if not vocab_detail:
            return jsonify({
                'success': False,
                'error': '词汇不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': vocab_detail
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/vocabulary/<int:vocab_id>/update', methods=['POST'])
def update_vocabulary_with_ai(vocab_id):
    """使用AI更新词汇信息"""
    try:
        user_id = SessionManager.get_user_id()
        vocab = VocabularyService.get_vocabulary_detail(vocab_id, user_id)
        
        if not vocab:
            return jsonify({
                'success': False,
                'error': '词汇不存在'
            }), 404
            
        # 使用AI更新词汇信息
        processor = ArticleProcessor()
        updated_info = processor.process_word(vocab['word'])
        
        if not updated_info:
            return jsonify({
                'success': False,
                'error': 'AI更新失败'
            }), 500
            
        # 更新词汇信息
        result = VocabularyService.update_vocabulary(vocab_id, updated_info)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/vocabulary/<int:vocab_id>', methods=['DELETE'])
def delete_vocabulary(vocab_id):
    """删除词汇"""
    try:
        VocabularyService.delete_vocabulary(vocab_id)
        
        return jsonify({
            'success': True,
            'message': '词汇删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/vocabulary')
def vocabulary_list():
    """词汇库页面"""
    return render_template('vocabulary/list.html')


@app.route('/vocabulary/learn')
def vocabulary_learn():
    """单词学习页面"""
    return render_template('vocabulary/learn.html')


@app.route('/api/vocabulary/learn/start', methods=['GET'])
def start_learning_session():
    """开始学习会话"""
    try:
        user_id = SessionManager.get_user_id()
        
        # 获取用户词汇库中的单词
        vocabularies = VocabularyService.get_user_vocabulary(
            user_id=user_id,
            filters={
                'limit': 10  # 每次最多学习10个单词
            }
        )
        
        if not vocabularies:
            return jsonify({
                'success': False,
                'error': '词汇库为空，请先添加单词'
            }), 404
            
        if len(vocabularies) < 4:
            return jsonify({
                'success': False,
                'error': f'词汇数量不足，当前只有{len(vocabularies)}个单词，至少需要4个单词才能开始学习'
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'words': vocabularies
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/vocabulary/learn/record', methods=['POST'])
def record_learning_result():
    """记录学习结果"""
    try:
        user_id = SessionManager.get_user_id()
        data = request.get_json()
        
        if not data or 'vocabulary_id' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        # 记录学习行为
        LearningRecord.record_action(
            user_id=user_id,
            vocabulary_id=data['vocabulary_id'],
            action_type='test',
            is_correct=data.get('is_correct'),
            response_time=data.get('response_time')
        )
        
        return jsonify({
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
