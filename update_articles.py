import logging
from datetime import datetime, timezone
import json
import os
from typing import Dict, List
import time
from original_scraper import OnePRScraper
from press_kit_scraper import PressKitScraper, EnhancedOnePRScraper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class DataUpdater:
    def __init__(self, data_file: str = 'articles.json'):
        self.data_file = data_file
        self.backup_dir = 'backups'
        os.makedirs(self.backup_dir, exist_ok=True)

    def load_existing_data(self) -> List[Dict]:
        """加载现有数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logging.error(f"Error loading existing data: {e}")
            return []

    def backup_data(self):
        """备份现有数据"""
        if not os.path.exists(self.data_file):
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{self.backup_dir}/articles_{timestamp}.json"
        try:
            import shutil
            shutil.copy2(self.data_file, backup_file)
            logging.info(f"Backup created: {backup_file}")

            # 保留最近30个备份
            backups = sorted(os.listdir(self.backup_dir))
            if len(backups) > 30:
                for old_backup in backups[:-30]:
                    os.remove(os.path.join(self.backup_dir, old_backup))
        except Exception as e:
            logging.error(f"Backup failed: {e}")

    def merge_and_save_data(self, new_articles: List[Dict], existing_data: List[Dict]):
        """合并新旧数据并保存"""
        # 用URL作为唯一标识
        existing_urls = {article['url'] for article in existing_data}
        
        # 合并数据，避免重复
        merged_data = existing_data + [
            article for article in new_articles
            if article['url'] not in existing_urls
        ]

        # 按发布日期排序
        merged_data.sort(
            key=lambda x: datetime.fromisoformat(x['published_date']),
            reverse=True
        )

        # 保存数据
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(merged_data)} articles to {self.data_file}")
        except Exception as e:
            logging.error(f"Error saving data: {e}")

    def generate_readme(self, articles: List[Dict]):
        """生成README文件"""
        readme_file = 'README.md'
        try:
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write('# 每日游戏新闻更新\n\n')
                f.write(f'**更新日期**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
                f.write('## 最新文章\n')
                
                for article in articles[:10]:  # 仅显示前10篇文章
                    f.write(f'### {article["title"]}\n')
                    f.write(f'![{article["title"]}]({article["image_url"]})\n')
                    f.write(f'发布于: {article["published_date"]}\n')
                    f.write(f'标签: {", ".join(article["tags"])}\n')
                    f.write(f'[下载 Press Kit]({article["press_kit_url"]})\n\n')
                
                f.write('## 更新进度\n')
                f.write('![更新进度](https://progress-bar.dev/100/)\n')
                
            logging.info(f"README.md 文件生成成功")
        except Exception as e:
            logging.error(f"生成 README.md 文件失败: {e}")

    def update(self):
        """执行更新流程"""
        try:
            logging.info("Starting data update process...")
            
            # 创建抓取器实例
            enhanced_scraper = EnhancedOnePRScraper()
            press_kit_scraper = PressKitScraper(max_workers=8)

            # 备份现有数据
            self.backup_data()

            # 加载现有数据
            existing_data = self.load_existing_data()
            logging.info(f"Loaded {len(existing_data)} existing articles")

            # 获取新数据
            combined_data = enhanced_scraper.get_articles_with_press_kits(press_kit_scraper)
            
            # 转换为可序列化的字典格式
            new_articles = []
            for article, press_kit in combined_data:
                article_dict = {
                    "url": article.url,
                    "title": article.title,
                    "image_url": article.image_url,
                    "published_date": article.published_date,
                    "tags": list(article.tags),
                    "press_kit_available": press_kit.has_press_kit,
                    "press_kit_url": press_kit.press_kit_url,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                new_articles.append(article_dict)

            # 记录抓取结果
            if new_articles:
                logging.info(f"Found {len(new_articles)} new articles")
            else:
                logging.warning("No new articles found. Continuing with existing data.")

            # 合并和保存数据
            self.merge_and_save_data(new_articles, existing_data)

            # 生成README文件
            self.generate_readme(new_articles + existing_data)

            # 无论是否有新文章，都返回成功
            return True

        except Exception as e:
            logging.error(f"Update process failed: {e}")
            return False

def main():
    updater = DataUpdater()
    success = updater.update()
    
    if success:
        logging.info("Update completed successfully")
    else:
        logging.error("Update failed")

if __name__ == "__main__":
    main()
