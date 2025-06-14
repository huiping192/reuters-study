import requests
from flask import Flask, render_template
from flask import request, jsonify

from audio_manager import generate_audio
from news_analytics import ArticleProcessor
from reuters_manager import get_reuters_news_with_subcategory, get_reuters_article, split_into_paragraphs
import urllib.parse
from flask import send_from_directory
import os

# 导入新增的模块
from models.database import init_db
from utils.session_manager import SessionManager
from services.vocabulary_service import VocabularyService

app = Flask(__name__)

# 配置session（简化版）
SessionManager.set_session_config(app)

# 初始化数据库
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
@app.route('/api/vocabulary', methods=['GET'])
def get_vocabulary():
    """获取词汇列表"""
    try:
        user_id = SessionManager.get_user_id()
        
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


if __name__ == '__main__':
    app.run(debug=True)
