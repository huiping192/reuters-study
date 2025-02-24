import requests
from flask import Flask, render_template
from flask import request, jsonify

from audio_manager import generate_audio
from news_analytics import ArticleProcessor
from reuters_manager import get_reuters_news_with_subcategory, get_reuters_article, split_into_paragraphs
import urllib.parse
from flask import send_from_directory
import os

app = Flask(__name__)

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
def handle_translate():
    data = request.get_json()
    try:
        if not data or 'text' not in data:
            return jsonify({'error': 'Invalid request format'}), 400

        # 验证文本内容
        input_text = data['text'].strip()
        if not input_text:
            return jsonify({'error': 'Empty text content'}), 400

        processor = ArticleProcessor()
        translated_text = processor.process_article(input_text)

        # 验证返回结果
        if not translated_text or not isinstance(translated_text, str):
            raise ValueError("Invalid translation result")

        print(f"Translation Result: {translated_text}")  # 添加类型验证
        return jsonify({
            'index': data.get('index', -1),
            'translation': translated_text
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


if __name__ == '__main__':
    app.run(debug=True)
