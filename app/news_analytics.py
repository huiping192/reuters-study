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

    def process_article(self, text: str, user_id=None, source_url=None):
        """处理整篇文章并返回结构化结果，同时收集词汇"""
        result = self._process_single_paragraph(text)
        
        # 如果提供了用户ID，则自动收集词汇
        if user_id and result.get('vocabulary'):
            self._collect_vocabulary(user_id, result['vocabulary'], source_url)
        
        return result

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
                if len(parts) >= 4:  # 确保至少有4个部分
                    result["vocabulary"].append({
                        "word": parts[0].strip(),
                        "pos": parts[1].strip(),
                        "def_cn": parts[2].strip(),
                        "example": parts[3].strip()  # 直接使用第四个部分作为例句
                    })

        # 解析翻译部分
        result["translation"] = trans_section.strip()

        return result

    def _collect_vocabulary(self, user_id, vocabulary_list, source_url=None):
        """收集词汇到用户词汇库"""
        try:
            from services.vocabulary_service import VocabularyService
            
            # 批量添加词汇
            result = VocabularyService.batch_add_vocabulary(
                user_id=user_id,
                vocab_list=vocabulary_list,
                source_url=source_url
            )
            
            print(f"词汇收集完成: 成功添加 {result['total_added']} 个词汇，失败 {result['total_errors']} 个")
            
            if result['errors']:
                for error in result['errors']:
                    print(f"词汇收集错误: {error['word']} - {error['error']}")
                    
        except Exception as e:
            print(f"词汇收集失败: {str(e)}")

    def _get_ai_response(self, text: str) -> ChatCompletion:
        """获取DeepSeek API响应"""
        system_prompt = """作为专业英语教学助手，请：
- 翻译为地道中文
- 识别1-5个CEFR C2/C1级别词汇
- 对每个词汇提供：
   - 发音
   - 词性
   - 中文释义
   - 例句

输出格式：

【Vocabulary】
单词｜词性｜中文释义｜例句
单词｜词性｜中文释义｜例句
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
