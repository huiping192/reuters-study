import os
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Tuple
from audio_manager import generate_audio


class TTSCacheService:
    """TTS缓存服务：管理单词和例句的音频缓存"""

    def __init__(self, db_path: str, tts_dir: str):
        self.db_path = db_path
        self.tts_dir = tts_dir
        self._init_db()

    def _init_db(self):
        """初始化缓存数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tts_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT UNIQUE NOT NULL,
                text_content TEXT NOT NULL,
                cache_type TEXT NOT NULL,
                audio_filename TEXT NOT NULL,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_text_hash ON tts_cache(text_hash)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cache_type ON tts_cache(cache_type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_last_accessed ON tts_cache(last_accessed_at)
        ''')
        conn.commit()
        conn.close()

    def _get_text_hash(self, text: str) -> str:
        """生成文本的MD5哈希"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get_or_create_audio(self, text: str, cache_type: str = 'word') -> Tuple[bool, str]:
        """
        获取或创建音频文件
        返回: (是否从缓存获取, 音频URL路径)
        """
        text_hash = self._get_text_hash(text)

        # 检查缓存
        cached_filename = self._get_cached_audio(text_hash)
        if cached_filename and os.path.exists(os.path.join(self.tts_dir, cached_filename)):
            # 更新访问记录
            self._update_access_record(text_hash)
            return True, f'/tts/{cached_filename}'

        # 生成新音频
        filename = generate_audio(text, self.tts_dir)

        # 记录到缓存数据库
        file_path = os.path.join(self.tts_dir, filename)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        self._save_cache_record(text_hash, text, cache_type, filename, file_size)

        return False, f'/tts/{filename}'

    def _get_cached_audio(self, text_hash: str) -> Optional[str]:
        """从数据库获取缓存的音频文件名"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT audio_filename FROM tts_cache WHERE text_hash = ?',
            (text_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def _save_cache_record(self, text_hash: str, text: str, cache_type: str,
                           filename: str, file_size: int):
        """保存缓存记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO tts_cache (text_hash, text_content, cache_type,
                                       audio_filename, file_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (text_hash, text, cache_type, filename, file_size))
            conn.commit()
        except sqlite3.IntegrityError:
            # 哈希冲突，更新记录
            cursor.execute('''
                UPDATE tts_cache
                SET audio_filename = ?, file_size = ?, last_accessed_at = CURRENT_TIMESTAMP
                WHERE text_hash = ?
            ''', (filename, file_size, text_hash))
            conn.commit()
        finally:
            conn.close()

    def _update_access_record(self, text_hash: str):
        """更新访问记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tts_cache
            SET last_accessed_at = CURRENT_TIMESTAMP,
                access_count = access_count + 1
            WHERE text_hash = ?
        ''', (text_hash,))
        conn.commit()
        conn.close()

    def clean_old_cache(self, days: int = 90, max_size_mb: int = 500):
        """
        清理过期缓存
        :param days: 删除超过N天未访问的文件
        :param max_size_mb: 缓存总大小上限（MB）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 删除过期文件（超过N天未访问）
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute('''
            SELECT audio_filename FROM tts_cache
            WHERE last_accessed_at < ?
        ''', (cutoff_date,))
        old_files = cursor.fetchall()

        deleted_count = 0
        for (filename,) in old_files:
            file_path = os.path.join(self.tts_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_count += 1

        cursor.execute('DELETE FROM tts_cache WHERE last_accessed_at < ?', (cutoff_date,))

        # 检查总容量，超过上限时删除最少使用的文件
        cursor.execute('SELECT SUM(file_size) FROM tts_cache')
        total_size = cursor.fetchone()[0] or 0
        max_size_bytes = max_size_mb * 1024 * 1024

        if total_size > max_size_bytes:
            # 按访问次数和最后访问时间排序，删除最少使用的文件
            cursor.execute('''
                SELECT audio_filename, file_size FROM tts_cache
                ORDER BY access_count ASC, last_accessed_at ASC
            ''')
            files = cursor.fetchall()

            size_to_free = total_size - max_size_bytes
            freed_size = 0

            for filename, file_size in files:
                if freed_size >= size_to_free:
                    break

                file_path = os.path.join(self.tts_dir, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    freed_size += file_size
                    deleted_count += 1

                cursor.execute('DELETE FROM tts_cache WHERE audio_filename = ?', (filename,))

        conn.commit()
        conn.close()

        return {
            'deleted_count': deleted_count,
            'total_size_mb': total_size / (1024 * 1024)
        }

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*), SUM(file_size) FROM tts_cache')
        total_count, total_size = cursor.fetchone()

        cursor.execute('SELECT COUNT(*) FROM tts_cache WHERE cache_type = ?', ('word',))
        word_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM tts_cache WHERE cache_type = ?', ('sentence',))
        sentence_count = cursor.fetchone()[0]

        conn.close()

        return {
            'total_count': total_count or 0,
            'word_count': word_count or 0,
            'sentence_count': sentence_count or 0,
            'total_size_mb': round((total_size or 0) / (1024 * 1024), 2)
        }
