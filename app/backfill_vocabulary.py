"""
批量补全生词本：中文释义缺失或列错位的单词，重新用 AI 查询并写回数据库

用法（Docker 容器内 /app 目录）:
    python backfill_vocabulary.py --dry-run     # 只列出待补全的词
    python backfill_vocabulary.py --limit 3     # 先试几个
    python backfill_vocabulary.py               # 全部

可重复执行：修好的词不再符合条件，失败的词下次重跑会继续处理。
"""
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from app import app
from models.vocabulary import Vocabulary
from news_analytics import ArticleProcessor
from services.vocabulary_service import VocabularyService

# 释义里只有词性标签，说明当初模型多输出了一列音标，解析时整行错位
POS_ONLY = re.compile(
    r'^((名词|动词|形容词|副词|介词|连词|代词|感叹词)(短语)?'
    r'|(n|v|adj|adv|prep|conj|pron|phr)\.?'
    r'|(noun|verb|adjective|adverb)( phrase)?)$',
    re.IGNORECASE
)


def is_broken(vocab):
    definition_cn = (vocab.definition_cn or '').strip()
    pos = (vocab.pos or '').strip()
    return not definition_cn or bool(POS_ONLY.match(definition_cn)) or pos[:1] in ('/', '[')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()

    with app.app_context():
        targets = [(v.id, v.word) for v in Vocabulary.query.order_by(Vocabulary.id) if is_broken(v)][:args.limit]
        print(f"待补全 {len(targets)} 个词", flush=True)
        if args.dry_run:
            print(', '.join(word for _, word in targets))
            return

        processor = ArticleProcessor()
        done = failed = 0
        # 免费模型单次约 10 秒，少量并发提速；写库只在主线程做，避免跨线程共享 session
        with ThreadPoolExecutor(args.workers) as pool:
            futures = {pool.submit(processor.process_word, word): (vocab_id, word) for vocab_id, word in targets}
            for future in as_completed(futures):
                vocab_id, word = futures[future]
                info = future.result()
                if info and info.get('definition_cn'):
                    VocabularyService.update_vocabulary(vocab_id, info)
                    done += 1
                    print(f"[{done + failed}/{len(targets)}] ✓ {word}: {info['definition_cn'][:40]}", flush=True)
                else:
                    failed += 1
                    print(f"[{done + failed}/{len(targets)}] ✗ {word}", flush=True)

        print(f"完成：成功 {done}，失败 {failed}" + ("（重跑即可继续）" if failed else ''), flush=True)


if __name__ == '__main__':
    main()
