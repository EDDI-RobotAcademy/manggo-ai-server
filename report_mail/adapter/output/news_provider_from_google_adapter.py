import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from report_mail.domain.news import News
from report_mail.application.port.news_provider_port import NewsProviderPort

class NewsProviderAdapter(NewsProviderPort):
    RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"

    def get_major_news(self) -> List[News]:
        try:
            response = requests.get(self.RSS_URL, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
            
            news_list = []
            for item in items[:10]: # Fetch top 10 first
                title = item.title.text if item.title else "No Title"
                link = item.link.text if item.link else ""
                pub_date_str = item.pubDate.text if item.pubDate else ""
                
                # Simple date parsing (RFC 822)
                try:
                    published_at = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                except ValueError:
                    published_at = datetime.now()

                news_list.append(News(title=title, link=link, published_at=published_at))
                
            return news_list
        except Exception as e:
            print(f"[ERROR] Failed to fetch news: {e}")
            return []
