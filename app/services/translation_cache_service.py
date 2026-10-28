import hashlib
import json
import sqlite3
from typing import Optional


class TranslationCacheService:
    """翻译缓存：同一段落只调用一次 AI，免费模型额度有限"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS translation_cache (
                    text_hash TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def _get_text_hash(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                'SELECT result_json FROM translation_cache WHERE text_hash = ?',
                (self._get_text_hash(text),)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def set(self, text: str, result: dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO translation_cache (text_hash, result_json) VALUES (?, ?)',
                (self._get_text_hash(text), json.dumps(result, ensure_ascii=False))
            )
