import os
import re
from openai import OpenAI
from openai.types.chat import ChatCompletion
from config import config


class ArticleProcessor:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
            timeout=120
        )

    def process_article(self, text: str) -> str:
        """处理整篇文章并返回结构化结果"""
        return self._process_single_paragraph(text)

    def _process_single_paragraph(self, text: str) -> str:
        """处理单个段落（移除<think>标签内容）"""
        raw_response = self._get_ai_response(text).choices[0].message.content

        # 使用正则表达式移除<think>标签及其内容
        cleaned_text = re.sub(
            r'<think>.*?</think>',  # 匹配<think>标签
            '',  # 替换为空字符串
            raw_response,  # 原始文本
            flags=re.DOTALL  # 允许跨行匹配
        )

        # 移除可能残留的空白行
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text).strip()

        return cleaned_text

    def _get_ai_response(self, text: str) -> ChatCompletion:
        """获取DeepSeek API响应"""
        system_prompt = """作为专业英语教学助手，请：
1. 翻译为地道中文
2. 识别1-5个难点单词,词汇
3. 对每个词汇提供：
   - 词性
   - 中文释义
   - 中英对照例句
4. Toeic 700分以上水平

输出格式：
1. 单词｜词性：释义
...

中文翻译: 翻译内容
"""

        return self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.2,
            max_tokens=2000,
            stream=False
        )
