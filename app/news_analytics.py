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

        # 按标记取段落，不依赖两段的先后顺序
        trans_match = re.search(r'【Translation】(.*?)(?=【Vocabulary】|$)', raw_response, re.S)
        vocab_match = re.search(r'【Vocabulary】(.*?)(?=【Translation】|$)', raw_response, re.S)
        if not trans_match:
            raise ValueError("AI 响应缺少【Translation】")
        trans_section = trans_match.group(1)

        # 解析词汇部分
        vocab_lines = [line.strip() for line in (vocab_match.group(1) if vocab_match else '').split("\n") if line.strip()]
        entries = []
        for line in vocab_lines:
            # 有的模型用半角 | 分隔
            if '｜' in line or '|' in line:
                entries.append([p.strip() for p in re.split(r'[｜|]', line)])
            elif entries and len(entries[-1]) == 3:
                # 有的模型把例句换行写在下一行
                entries[-1].append(line)

        for parts in entries:
            if len(parts) == 3 and re.match(r'[A-Z]', parts[2]):
                # 词性和释义挤在同一列：单词｜adj.（…）释义｜例句
                m = re.match(r'([a-zA-Z]+\.)\s*(.+)', parts[1])
                parts = [parts[0], m.group(1), m.group(2), parts[2]] if m else [parts[0], '', parts[1], parts[2]]
            # 部分模型会多输出一列音标(单词｜音标｜词性｜释义｜例句)，不处理会导致整行错位
            pronunciation = parts.pop(1) if len(parts) >= 5 and parts[1][:1] in ('/', '[') else ''
            if len(parts) >= 4:  # 确保至少有4个部分
                result["vocabulary"].append({
                    # 部分模型(如 gemma)会给单词加 Markdown 粗体
                    "word": parts[0].strip('*').strip(),
                    "pos": parts[1],
                    "def_cn": parts[2],
                    "example": parts[3],  # 直接使用第四个部分作为例句
                    "pronunciation": pronunciation
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

    def _model_kwargs(self) -> dict:
        models = [m.strip() for m in config.OPENAI_MODEL.split(',') if m.strip()]
        kwargs = {"model": models[0]}
        if 'openrouter.ai' in config.OPENAI_BASE_URL:
            # 翻译查词不需要推理；推理型免费模型会把 token 耗在思考上，慢且可能截断
            extra_body = {"reasoning": {"enabled": False}}
            if len(models) > 1:
                # OpenRouter 的 models 参数：免费模型常被上游限流(429)，自动换下一个；超过 3 个会直接 400
                extra_body["models"] = models[:3]
            kwargs["extra_body"] = extra_body
        return kwargs

    def _get_ai_response(self, text: str) -> ChatCompletion:
        """获取DeepSeek API响应"""
        # 输出 token 数决定耗时，限制例句长度、禁止多余说明
        system_prompt = """你是英语教学助手。先把用户给的英文翻译成地道中文，再挑出其中1-5个 CEFR C1/C2 词汇。
严格按以下格式输出，每个词汇占一行、四项都写在同一行，不要任何多余说明：

【Translation】
中文译文

【Vocabulary】
单词｜词性｜中文释义｜例句(15词以内的简短英文句子)
"""

        return self.client.chat.completions.create(
            **self._model_kwargs(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.2,
            max_tokens=2000,
            stream=False
        )

    def process_word(self, word: str) -> dict:
        """处理单个单词，获取详细信息"""
        system_prompt = """作为专业英语教学助手，请分析这个单词并提供以下信息：
- 词性 (POS)
- 中文释义
- 英文释义
- 例句
- 难度等级 (CEFR)
- 发音

输出格式：
POS: 词性
DEF_CN: 中文释义
DEF_EN: 英文释义
EXAMPLE: 例句
LEVEL: 难度等级
PRON: 发音
"""

        try:
            response = self.client.chat.completions.create(
                **self._model_kwargs(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": word}
                ],
                temperature=0.2,
                max_tokens=1000,
                stream=False
            )

            # 解析响应
            content = response.choices[0].message.content
            result = {}
            
            fields = {
                'pos': 'pos',
                'def_cn': 'definition_cn',
                'def_en': 'definition_en',
                'example': 'example',
                'level': 'difficulty_level',
                'pron': 'pronunciation',
            }
            current = None

            # 解析每一行
            for line in content.split('\n'):
                key, sep, value = line.partition(':')
                # 兼容 "**POS:** verb" 这类 Markdown 粗体输出
                key = key.strip().strip('*').lower()
                if sep and key in fields:
                    current = fields[key]
                    result[current] = value.strip().strip('*').strip()
                elif current and line.strip():
                    # 多义词时模型会把内容换行写在字段名下面
                    result[current] = (result[current] + '\n' + line.strip()).strip()

            if 'difficulty_level' in result:
                # 模型常附带解释，如 "B2 (Upper Intermediate)"；生词本按等级精确筛选和统计
                level = re.search(r'[ABC][12]', result['difficulty_level'])
                result['difficulty_level'] = level.group(0) if level else ''

            return result

        except Exception as e:
            print(f"处理单词失败: {str(e)}")
            return None
