"""
Reuters Study MCP Server
让 AI 助手能访问新闻和词汇数据
"""
import sqlite3
import os
import sys
import json
import feedparser
import requests
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 数据库路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "vocabulary.db")
DEFAULT_USER_ID = "single_user"

mcp = FastMCP("reuters-study")


# ─── 词汇工具 ───────────────────────────────────────────────

@mcp.tool()
def get_vocabulary(
    search: str = "",
    difficulty_level: str = "",
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> str:
    """
    查询词汇本。返回用户保存的单词列表。

    Args:
        search: 搜索关键词（匹配单词、中文释义、英文释义）
        difficulty_level: CEFR等级过滤，如 A1/A2/B1/B2/C1/C2
        sort_by: 排序字段 created_at / word / frequency / updated_at
        sort_order: asc 或 desc
        limit: 返回数量，默认50
        offset: 跳过数量，用于分页
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    where_clauses = ["user_id = ?"]
    params = [DEFAULT_USER_ID]

    if search:
        where_clauses.append(
            "(word LIKE ? OR definition_cn LIKE ? OR definition_en LIKE ?)"
        )
        term = f"%{search}%"
        params += [term, term, term]

    if difficulty_level:
        where_clauses.append("difficulty_level = ?")
        params.append(difficulty_level)

    valid_sort = {"created_at", "word", "frequency", "updated_at"}
    sort_col = sort_by if sort_by in valid_sort else "created_at"
    order = "ASC" if sort_order.lower() == "asc" else "DESC"

    sql = f"""
        SELECT word, pos, definition_cn, definition_en, example,
               difficulty_level, frequency, source_url, created_at
        FROM vocabulary
        WHERE {' AND '.join(where_clauses)}
        ORDER BY {sort_col} {order}
        LIMIT ? OFFSET ?
    """
    params += [limit, offset]
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return json.dumps(rows, ensure_ascii=False, indent=2)


@mcp.tool()
def get_vocabulary_stats() -> str:
    """
    获取词汇本统计信息：总词数、最近7天新增、按CEFR难度分布、出现频率最高的词。
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM vocabulary WHERE user_id = ?", (DEFAULT_USER_ID,))
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM vocabulary WHERE user_id = ? AND created_at >= date('now','-7 days')",
        (DEFAULT_USER_ID,),
    )
    recent = cur.fetchone()[0]

    cur.execute(
        "SELECT difficulty_level, COUNT(*) FROM vocabulary WHERE user_id = ? GROUP BY difficulty_level",
        (DEFAULT_USER_ID,),
    )
    difficulty = dict(cur.fetchall())

    cur.execute(
        "SELECT word, frequency FROM vocabulary WHERE user_id = ? ORDER BY frequency DESC LIMIT 10",
        (DEFAULT_USER_ID,),
    )
    top_words = [{"word": r[0], "frequency": r[1]} for r in cur.fetchall()]

    conn.close()
    result = {
        "total_words": total,
        "added_last_7_days": recent,
        "difficulty_distribution": difficulty,
        "top_frequency_words": top_words,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


# ─── 新闻工具 ───────────────────────────────────────────────

BBC_FEEDS = {
    "top": "http://feeds.bbci.co.uk/news/rss.xml",
    "world": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "technology": "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "science": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "health": "http://feeds.bbci.co.uk/news/health/rss.xml",
}


@mcp.tool()
def get_latest_news(category: str = "top", limit: int = 10) -> str:
    """
    获取最新 BBC 新闻列表。

    Args:
        category: top / world / technology / business / science / health
        limit: 返回条数，默认10
    """
    url = BBC_FEEDS.get(category, BBC_FEEDS["top"])
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:limit]:
        articles.append(
            {
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
            }
        )
    return json.dumps(articles, ensure_ascii=False, indent=2)


@mcp.tool()
def get_news_article(url: str) -> str:
    """
    获取某篇 BBC 新闻文章的正文内容。

    Args:
        url: 文章 URL（从 get_latest_news 获取）
    """
    from bs4 import BeautifulSoup

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; reuters-study-mcp/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # BBC 文章正文在 article 标签里
        article = soup.find("article")
        if not article:
            article = soup

        # 提取段落
        paragraphs = [p.get_text().strip() for p in article.find_all("p") if p.get_text().strip()]
        title_tag = soup.find("h1")
        title = title_tag.get_text().strip() if title_tag else ""

        result = {
            "url": url,
            "title": title,
            "content": "\n\n".join(paragraphs),
            "word_count": len(" ".join(paragraphs).split()),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "url": url})


if __name__ == "__main__":
    mcp.run()
