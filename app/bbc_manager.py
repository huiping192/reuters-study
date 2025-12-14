import requests
import feedparser
from bs4 import BeautifulSoup
from collections import defaultdict
from typing import List
from datetime import datetime


def get_bbc_news_with_category(max_news=20):
    """
    从BBC RSS Feed获取新闻列表
    返回格式与reuters_manager保持一致
    """
    feeds = {
        'World': 'http://feeds.bbci.co.uk/news/world/rss.xml',
        'Business': 'http://feeds.bbci.co.uk/news/business/rss.xml',
        'Technology': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
        'Science': 'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
    }

    categorized_news = defaultdict(lambda: defaultdict(list))

    for main_category, feed_url in feeds.items():
        try:
            feed = feedparser.parse(feed_url)

            if not feed.entries:
                print(f"警告: {main_category} 分类未获取到新闻")
                continue

            for entry in feed.entries[:max_news]:
                # 解析发布时间
                published = entry.get('published', '')
                try:
                    dt = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                    date_str = dt.strftime('%Y-%m-%d')
                except:
                    date_str = published

                news_entry = {
                    'title': entry.title,
                    'url': entry.link,
                    'category': main_category,
                    'sub_category': 'General',
                    'date': date_str
                }

                categorized_news[main_category]['General'].append(news_entry)

        except Exception as e:
            print(f"获取 {main_category} 新闻失败: {e}")
            continue

    return categorized_news


def get_bbc_article(url):
    """
    抓取BBC文章详情页完整内容
    返回格式与reuters_manager保持一致
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取标题
        title = None
        title_selectors = [
            soup.find('h1', {'id': 'main-heading'}),
            soup.find('h1'),
        ]
        for title_elem in title_selectors:
            if title_elem:
                title = title_elem.get_text(strip=True)
                break

        if not title:
            raise ValueError("无法提取文章标题")

        # 提取内容段落
        # BBC使用 data-component="text-block" 或普通 p 标签
        content_blocks = []

        # 方法1: 查找 data-component="text-block"
        text_blocks = soup.find_all('div', {'data-component': 'text-block'})
        if text_blocks:
            for block in text_blocks:
                # 在text-block中查找p标签
                paragraphs = block.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:  # 过滤太短的文本
                        content_blocks.append(text)

        # 方法2: 如果方法1失败，直接查找article内的p标签
        if not content_blocks:
            article_elem = soup.find('article')
            if article_elem:
                paragraphs = article_elem.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        content_blocks.append(text)

        # 方法3: 兜底方案，查找所有p标签
        if not content_blocks:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 30:  # 更严格的过滤
                    content_blocks.append(text)

        if not content_blocks:
            raise ValueError("无法提取文章内容")

        return {
            "title": title,
            "content": "\n\n".join(content_blocks)
        }

    except Exception as e:
        print(f"获取BBC文章失败: {e}")
        return None


def split_into_paragraphs(text: str) -> List[str]:
    """
    段落分割（与reuters_manager保持一致）
    """
    MIN_PARAGRAPH_LENGTH = 100
    MAX_PARAGRAPH_LENGTH = 300

    raw_paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    merged = []
    buffer = ""

    for p in raw_paragraphs:
        if len(buffer) + len(p) < MAX_PARAGRAPH_LENGTH:
            buffer += " " + p if buffer else p
        else:
            if buffer:
                merged.append(buffer)
            buffer = p

    if buffer:
        merged.append(buffer)

    return [p for p in merged if len(p) >= MIN_PARAGRAPH_LENGTH]


if __name__ == "__main__":
    # 测试代码
    print("测试BBC新闻抓取...")
    print("=" * 80)

    # 测试新闻列表
    news = get_bbc_news_with_category()
    print(f"获取到 {len(news)} 个新闻分类")
    for cat, sub_cats in news.items():
        for sub_cat, items in sub_cats.items():
            print(f"  {cat} - {sub_cat}: {len(items)} 条新闻")
            if items:
                print(f"    示例: {items[0]['title'][:60]}...")

    # 测试文章详情
    if news:
        first_category = list(news.keys())[0]
        first_item = news[first_category]['General'][0]
        print(f"\n测试文章详情: {first_item['title'][:50]}...")
        article = get_bbc_article(first_item['url'])
        if article:
            print(f"  ✓ 标题: {article['title'][:50]}...")
            print(f"  ✓ 内容长度: {len(article['content'])} 字符")
            paragraphs = split_into_paragraphs(article['content'])
            print(f"  ✓ 段落数: {len(paragraphs)}")
