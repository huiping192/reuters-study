import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict
from typing import List
def get_reuters_article(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.reuters.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        with requests.Session() as session:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title = soup.find('h1', {'data-testid': 'Heading'}).get_text(strip=True)

            # 精准定位所有段落（通过 data-testid 前缀）
            paragraphs = soup.find_all('div', {'data-testid': lambda x: x and x.startswith('paragraph-')})

            # 清理内容：保留段落文本（含链接文字），去除空行
            content = []
            for p in paragraphs:
                text = p.get_text(separator=' ', strip=True)  # 合并链接文本与正文
                if text:
                    content.append(text)

            return {
                "title": title,
                "content": "\n\n".join(content)
            }

    except Exception as e:
        print(f"Error: {e}")
        return None


def get_news_category_info(url):
    """提取分类信息（仅当 URL 中存在明确的子分类层级时）"""
    path = urlparse(url).path
    segments = [s for s in path.split('/') if s and not s.replace('-', '').isdigit()]  # 过滤空段和日期段

    main_category = segments[0].title() if len(segments) > 0 else "Other"
    sub_category = None

    # 仅在路径结构为 /category/subcategory/... 时提取子分类
    if len(segments) >= 2 and '-' not in segments[1] and len(segments[1]) <= 20:
        sub_category = segments[1].title()

    return {
        "category": main_category,
        "sub_category": sub_category
    }


def get_reuters_news_with_subcategory(homepage_url="https://www.reuters.com/", max_news=20):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        with requests.Session() as session:
            response = session.get(homepage_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('a', {'data-testid': 'TitleLink'})

            categorized_news = defaultdict(lambda: defaultdict(list))

            for item in news_items[:max_news]:
                title = item.find('span', {'data-testid': 'TitleHeading'}).get_text(strip=True)
                relative_url = item['href']
                absolute_url = urljoin(homepage_url, relative_url)

                category_info = get_news_category_info(relative_url)

                news_entry = {
                    "title": title,
                    "url": absolute_url,
                    **category_info
                }

                main_cat = category_info['category']
                sub_cat = category_info['sub_category']
                if sub_cat:
                    categorized_news[main_cat][sub_cat].append(news_entry)
                else:
                    categorized_news[main_cat]["General"].append(news_entry)

            return categorized_news

    except Exception as e:
        print(f"Error: {str(e)}")
        return defaultdict(dict)

def split_into_paragraphs(text: str) -> List[str]:
    """预处理段落合并短段落"""

    MIN_PARAGRAPH_LENGTH = 100
    MAX_PARAGRAPH_LENGTH = 300
    raw_paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    merged = []
    buffer = ""

    for p in raw_paragraphs:
        if len(buffer) + len(p) < MAX_PARAGRAPH_LENGTH:
            buffer += " " + p
        else:
            if buffer:
                merged.append(buffer)
            buffer = p

    if buffer:
        merged.append(buffer)

    return [p for p in merged if len(p) >= MIN_PARAGRAPH_LENGTH]


if __name__ == "__main__":
    url = "https://www.reuters.com/world/europe/zelenskiy-calls-european-army-deter-russia-earn-us-respect-2025-02-15/"
    article = get_reuters_article(url)

    if article:
        print(f"标题: {article['title']}\n")
        print("正文内容:")
        print(article['content'])
    else:
        print("抓取失败")
