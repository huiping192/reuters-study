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

    def process_article(self, text: str):
        """处理整篇文章并返回结构化结果"""
        return self._process_single_paragraph(text)

    def _process_single_paragraph(self, text: str):
        """处理单个段落（移除<think>标签内容）"""
        raw_response = self._get_ai_response(text).choices[0].message.content
        print(f"AI Response: {raw_response}")
        result = {
            "vocabulary": [],
            "translation": ""
        }

        # 分割词汇和翻译部分
        vocab_section, trans_section = raw_response.split("【Translation】")

        # 解析词汇部分
        vocab_lines = [line.strip() for line in vocab_section.split("【Vocabulary】")[1].split("\n") if line.strip()]
        for line in vocab_lines:
            if line and '｜' in line:
                parts = line.split('｜')
                if len(parts) >= 4:
                    result["vocabulary"].append({
                        "word": parts[0].strip(),
                        "pos": parts[1].strip(),
                        "def_cn": parts[2].strip(),
                        "example": parts[3].strip()
                    })

        # 解析翻译部分
        result["translation"] = trans_section.strip()

        return result

    def _get_ai_response(self, text: str) -> ChatCompletion:
        """获取DeepSeek API响应"""
        system_prompt = """作为专业英语教学助手，请：
1. 翻译为地道中文
2. 识别1-5个难点单词,词汇
3. 对每个词汇提供：
   - 词性
   - 中文释义
   - 例句
4. Toeic 700分以上水平

输出格式：

【Vocabulary】
1. 单词｜词性｜中文释义｜例句
2. 单词｜词性｜中文释义｜例句
...

【Translation】
翻译内容
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
