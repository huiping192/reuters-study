"""游戏对白整句翻译 + 生词语境释义，走网站同一套 OpenRouter 配置。

调用方（obs-game-lookup 的 Mac 服务）在按键后等结果，宁可超时返回错误（只显示词典释义）也不要让它干等，所以不重试。
"""
import json
import os
import re

from news_analytics import ArticleProcessor

PROMPT = """你是游戏英语学习助手。给你一句游戏对白和其中的生词，返回 JSON：
{"translation": "整句自然的简体中文翻译", "words": {"生词": "该词在这句话里的中文意思，不超过8个字"}}
context 是同一场景前几句对白，仅用来理解指代和语气，不要翻译它。
只返回 JSON。"""

TIMEOUT = float(os.getenv('GAME_TRANSLATE_TIMEOUT', '8'))
# 网站为了快把小模型排第一，但它译不出游戏梗（108 个烦恼、@channel），游戏要大模型优先
MODEL = os.getenv('GAME_TRANSLATE_MODEL')


class GameTranslateService:
    _processor = None

    @classmethod
    def translate(cls, text, context, words):
        if cls._processor is None:
            cls._processor = ArticleProcessor()
        p = cls._processor
        payload = {'context': list(context), 'text': text, 'words': list(words)}
        # 免费模型 429 时默认会重试两次，调用方等不了那么久
        resp = p.client.with_options(timeout=TIMEOUT, max_retries=0).chat.completions.create(
            **p._model_kwargs(MODEL),
            messages=[{'role': 'system', 'content': PROMPT},
                      {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}],
            temperature=0.2,
            max_tokens=500,
        )
        content = resp.choices[0].message.content or ''
        # 部分免费模型不支持 JSON 模式，会包上 ```json 或前后加说明
        match = re.search(r'\{.*\}', content, re.S)
        if not match:
            raise ValueError(f'模型没有返回 JSON: {content[:100]}')
        data = json.loads(match.group())
        return data.get('translation'), data.get('words') or {}
