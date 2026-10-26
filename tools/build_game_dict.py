"""把 ECDICT 官方 stardict.db 精简成游戏查词用的 game_dict.db。

用法: python tools/build_game_dict.py <stardict.db> <game_dict.db>
"""
import sqlite3
import sys

# 短语只收 ≤3 词且每个词都常用的，否则 200 万条短语会撑大文件
PHRASE_MAX_WORDS = 3
PHRASE_MAX_RANK = 20000


def build(src_path, dst_path):
    src = sqlite3.connect(src_path)
    dst = sqlite3.connect(dst_path)
    dst.executescript("""
        DROP TABLE IF EXISTS dict;
        CREATE TABLE dict (
            word TEXT PRIMARY KEY COLLATE NOCASE,
            phonetic TEXT, pos TEXT, translation TEXT,
            lemma TEXT, rank INTEGER, collins INTEGER, oxford INTEGER, tag TEXT
        ) WITHOUT ROWID;
    """)

    # frq 是当代语料词频排名，越小越常用；0/NULL 表示无数据
    rank_of = {}
    rows = []
    for word, phonetic, pos, trans, exchange, frq, bnc, collins, oxford, tag in src.execute(
        "SELECT word, phonetic, pos, translation, exchange, frq, bnc, collins, oxford, tag "
        "FROM stardict WHERE translation IS NOT NULL AND translation <> ''"
    ):
        rank = frq or bnc or 0
        lemma = None
        for part in (exchange or '').split('/'):
            if part.startswith('0:'):
                lemma = part[2:]
        is_phrase = ' ' in word
        if not is_phrase and (rank or collins or oxford or tag):
            rows.append((word, phonetic, pos, trans, lemma, rank, collins or 0, oxford or 0, tag))
            rank_of[word.lower()] = rank
        elif is_phrase and word.count(' ') < PHRASE_MAX_WORDS and not trans.lstrip().startswith('[网络]'):
            # [网络] 开头的是网页抓取的词条，质量很差
            rows.append((word, phonetic, pos, trans, None, 0, 0, 0, tag))

    kept = []
    for r in rows:
        if ' ' in r[0]:
            if not all(0 < rank_of.get(w.lower(), 0) <= PHRASE_MAX_RANK for w in r[0].split()):
                continue
        kept.append(r)

    # 词典里 vowed 这类变形词常常没有独立词条，只在原形的 exchange 里出现
    have = {r[0].lower() for r in kept}
    for word, phonetic, pos, trans, exchange, frq, bnc, collins, oxford, tag in src.execute(
        "SELECT word, phonetic, pos, translation, exchange, frq, bnc, collins, oxford, tag "
        "FROM stardict WHERE exchange IS NOT NULL AND exchange <> '' AND word NOT LIKE '% %'"
    ):
        if word.lower() not in rank_of:
            continue
        for part in exchange.split('/'):
            kind, _, form = part.partition(':')
            if kind != '0' and form and ' ' not in form and form.lower() not in have:
                have.add(form.lower())
                kept.append((form, phonetic, pos, trans, word, rank_of[word.lower()],
                             collins or 0, oxford or 0, tag))

    dst.executemany("INSERT OR IGNORE INTO dict VALUES (?,?,?,?,?,?,?,?,?)", kept)
    dst.commit()
    dst.execute("VACUUM")
    print(f"{dst.execute('SELECT COUNT(*) FROM dict').fetchone()[0]} entries")


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
