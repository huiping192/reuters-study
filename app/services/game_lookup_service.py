"""游戏对白查词：本地词典 + 已知词过滤，不调用 LLM。"""
import os
import re
import sqlite3

from models.database import db
from models.learning_record import LearningRecord
from models.vocabulary import Vocabulary

DICT_PATH = os.getenv(
    'GAME_DICT_PATH',
    os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'game_dict.db'))

KNOWN_RANK = int(os.getenv('GAME_KNOWN_RANK', '3000'))
MASTERED_LEVEL = 4
MAX_PHRASE_WORDS = 3

TOKEN_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SENTENCE_BOUNDARY_RE = re.compile(r"(?:^|[.!?]['\"”]?\s+)$")

# 以虚词开头的短语（the end、be found）词典里也有，匹配上只会制造噪音
FUNCTION_WORDS = frozenset(
    "a an the i me my you your he him his she her it its we us our they them their "
    "this that these those am is are was were be been being do does did have has had "
    "will would shall should can could may might must to of in on at by for with from "
    "and or but not no so if as than then there here what who how when where".split())


class GameLookupService:
    _conn = None

    @classmethod
    def _dict(cls):
        if cls._conn is None:
            # 只读打开，避免容器里误写词典文件
            cls._conn = sqlite3.connect(
                f"file:{os.path.abspath(DICT_PATH)}?mode=ro", uri=True, check_same_thread=False)
            cls._conn.row_factory = sqlite3.Row
        return cls._conn

    @classmethod
    def _entry(cls, word):
        return cls._dict().execute("SELECT * FROM dict WHERE word = ?", (word,)).fetchone()

    @staticmethod
    def _mastered_words(user_id):
        rows = db.session.query(Vocabulary.word).join(
            LearningRecord, LearningRecord.vocabulary_id == Vocabulary.id
        ).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.action_type == 'master',
            LearningRecord.mastery_level >= MASTERED_LEVEL,
        ).distinct().all()
        return {r[0] for r in rows}

    @classmethod
    def _find_phrases(cls, tokens, joined):
        """最长匹配优先，返回 {起始下标: (长度, 词条)}。joined[i] 表示 tokens[i] 与前一词之间没有标点。"""
        found = {}
        lowered = [t.lower() for t in tokens]
        i = 0
        while i < len(lowered):
            for n in range(min(MAX_PHRASE_WORDS, len(lowered) - i), 1, -1):
                words = lowered[i:i + n]
                if (words[0] in FUNCTION_WORDS or not all(joined[i + 1:i + n])
                        or any(t[0].isupper() for t in tokens[i:i + n][1:])):
                    continue
                entry = cls._entry(' '.join(words))
                if entry:
                    found[i] = (n, entry)
                    break
            i += found[i][0] if i in found else 1
        return found

    @classmethod
    def lookup(cls, user_id, text, source=None):
        matches = list(TOKEN_RE.finditer(text))
        raw = [m.group() for m in matches]
        joined = [i > 0 and text[matches[i - 1].end():m.start()].strip() == ''
                  for i, m in enumerate(matches)]
        # 句首大写是语法需要，不代表专有名词
        sentence_start = {i for i, m in enumerate(matches)
                          if SENTENCE_BOUNDARY_RE.search(text[:m.start()])}
        mastered = cls._mastered_words(user_id)
        phrases = cls._find_phrases(raw, joined)

        items, unresolved, seen = [], [], set()
        i = 0
        while i < len(raw):
            if i in phrases:
                n, entry = phrases[i]
                item = cls._item(' '.join(raw[i:i + n]), entry['word'], entry, 'phrase')
                i += n
            else:
                token = raw[i]
                skip_proper = token[0].isupper() and i not in sentence_start
                i += 1
                if skip_proper or "'" in token or len(token) < 3 or token.lower() in FUNCTION_WORDS:
                    continue
                entry = cls._entry(token.lower())
                lemma = (entry['lemma'] if entry and entry['lemma'] else token.lower())
                lemma_entry = cls._entry(lemma) or entry
                if not lemma_entry:
                    unresolved.append(token)
                    continue
                rank = lemma_entry['rank']
                if (0 < rank <= KNOWN_RANK) or lemma in mastered:
                    continue
                item = cls._item(token, lemma, lemma_entry, 'word')
            if item['lemma'] in seen:
                continue
            seen.add(item['lemma'])
            items.append(item)

        for item in items:
            cls._record(user_id, item, text, source)
        return items, unresolved

    @staticmethod
    def _item(surface, lemma, entry, kind):
        return {
            'surface': surface,
            'lemma': lemma,
            'kind': kind,
            'phonetic': entry['phonetic'],
            'pos': entry['pos'],
            'translation': entry['translation'],
            'rank': entry['rank'],
        }

    @staticmethod
    def _record(user_id, item, sentence, source):
        word = item['lemma'].lower()
        existing = Vocabulary.query.filter_by(user_id=user_id, word=word).first()
        if existing:
            # 不覆盖 LLM 已生成的释义和例句，只累加出现次数
            existing.increment_frequency()
            db.session.commit()
            return
        Vocabulary.add_or_update_vocabulary(user_id, {
            'word': word,
            'definition_cn': item['translation'],
            'pronunciation': item['phonetic'],
            'example': sentence,
            'source_url': f'game:{source}' if source else 'game',
        })
