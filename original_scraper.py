
#2025-02-24 08:37:29        
        
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import os
from typing import Dict, List, Optional, Set
import time
from dataclasses import dataclass, asdict, field
from datetime import timezone, timedelta

@dataclass
class Article:
    url: str
    title: str
    image_url: str
    published_date: str
    tags: Set[str] = field(default_factory=set)  # 使用 Set 来存储标签，避免重复

    def __str__(self):
        return f"\nArticle:\n  Title: {self.title}\n  URL: {self.url}\n  Image: {self.image_url}\n  Published: {self.published_date}\n  Tags: {self.tags}"


        
class OnePRScraper:
    def __init__(self, base_url: str = "http://www.oneprstudio.com"):
        self.base_url = base_url
        self.data_file = "last_scrape.json"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def load_last_scrape_data(self) -> Optional[datetime]:
        """加载上次抓取的最新文章日期"""
        if not os.path.exists(self.data_file):
            return None
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return datetime.fromisoformat(data['last_article_date'])
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def save_last_scrape_data(self, last_date: datetime):
        """保存最新文章日期"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'last_article_date': last_date.isoformat(),
                'last_scrape': datetime.now(timezone.utc).isoformat()
            }, f)

    def parse_article(self, article_elem) -> Optional[Article]:
        """解析文章元素"""
        try:
            # 获取链接和标题
            link_elem = article_elem.find('a', href=True)
            if not link_elem:
                return None
            
            url = link_elem['href']
            title = link_elem.get('title', '')
            
            # 获取图片URL
            img_elem = article_elem.find('img')
            image_url = img_elem['src'] if img_elem else ''
            
            # 获取发布日期
            date_meta = article_elem.find('meta', {'itemprop': 'datePublished'})
            if not date_meta:
                return None
                
            published_date = date_meta['content']
            tags = set()
            article_class = article_elem.get('class', [])
            for class_name in article_class:
                if class_name.startswith('tag-'):
                    # 去除 'tag-' 前缀，将标签添加到集合中
                    tags.add(class_name[4:])
            
            return Article(url=url, title=title, image_url=image_url, published_date=published_date, tags=tags)
        except Exception as e:
            print(f"Error parsing article: {e}")
            return None

    def get_articles_from_page(self, page_num: int) -> List[Article]:
        """获取指定页面的文章"""
        url = f"{self.base_url}/news/page/{page_num}/"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            for article_elem in soup.find_all('article'):
                article = self.parse_article(article_elem)
                if article:
                    articles.append(article)
            
            return articles
        except requests.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            pass
        continue
           # return []

    def get_new_articles(self) -> List[Article]:
        """获取所有新文章"""
        last_scrape_date = self.load_last_scrape_data()
        new_articles = []
        page_num = 1
        latest_date = None
        
        while True:
            articles = self.get_articles_from_page(page_num)
            
            if not articles:
                break
                
            # 更新最新的文章日期
            if page_num == 1 and articles:
                latest_date = datetime.fromisoformat(articles[0].published_date)
            
            # 检查是否有新文章
            for article in articles:
                article_date = datetime.fromisoformat(article.published_date)
                
                if last_scrape_date and article_date <= last_scrape_date:
                    # 如果找到已经抓取过的文章，停止搜索
                    return new_articles

                new_articles.append(article)

            print(new_articles)
            # 防止过快请求
            time.sleep(1)
            page_num += 1
            if page_num > 3:
                break #翻页获取，page_num > 2:为获取1页，10为获取9页
            print(f"获取{page_num} 页中")
        
        # 保存最新的抓取日期
        if latest_date:
            self.save_last_scrape_data(latest_date)
            """
        print("\nCollected articles:")  # 添加收集到的文章列表
        for idx, article in enumerate(new_articles, 1):
            print(f"\n{idx}. {article}")
            """

        return new_articles
