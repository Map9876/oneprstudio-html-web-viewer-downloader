# 新增独立模块：press_kit_scraper.py
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple
import concurrent.futures
from dataclasses import dataclass
from original_scraper import Article, OnePRScraper # 假设原始类在original_scraper.py

@dataclass
class PressKitInfo:
    url: str
    has_press_kit: bool
    press_kit_url: Optional[str] = None

class PressKitScraper:
    def __init__(self, max_workers: int = 5, timeout: int = 10):
        self.max_workers = max_workers
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def _get_press_kit_single(self, article: Article) -> PressKitInfo:
        """独立获取单个文章的Press Kit信息"""
        try:
            response = requests.get(
                article.url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            press_kit_link = soup.select_one('div.entry-content a.btn-shortcode[href]')
            
            return PressKitInfo(
                url=article.url,
                has_press_kit=press_kit_link is not None,
                press_kit_url=press_kit_link['href'] if press_kit_link else None
            )
        except Exception as e:
            print(f"Error processing {article.url}: {str(e)}")
            return PressKitInfo(
                url=article.url,
                has_press_kit=False,
                press_kit_url=None
            )

    def get_press_kits(self, articles: List[Article]) -> List[PressKitInfo]:
        """批量获取Press Kit信息（线程池版本）"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._get_press_kit_single, article): article
                for article in articles
            }
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        return results

# 原始代码增强版（original_scraper.py）
# 保持原始类不变，仅添加类型提示
class EnhancedOnePRScraper(OnePRScraper):
    def get_articles_with_press_kits(self, press_kit_scraper: PressKitScraper) -> List[Tuple[Article, PressKitInfo]]:
        """组合使用获取文章+Press Kit信息"""
        articles = super().get_new_articles()
        print(articles)
        
        press_kits = press_kit_scraper.get_press_kits(articles)
        return list(zip(articles, press_kits))
