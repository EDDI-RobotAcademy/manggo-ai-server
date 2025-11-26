import os
import requests
from datetime import datetime
from typing import List
from report_mail.domain.news import News
from report_mail.application.port.news_provider_port import NewsProviderPort

class NewsProviderFromNaverAdapter(NewsProviderPort):
    NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"

    def get_major_news(self) -> List[News]:
        client_id = os.getenv("NAVER_CLIENT_ID")
        client_secret = os.getenv("NAVER_CLIENT_SECRET")

        if not client_id or not client_secret:
            print("[ERROR] Naver API credentials not set.")
            return []

        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }

        params = {
            "query": "오늘 뉴스 속보",
            "display": 10,
            "start": 1,
            "sort": "sim"
        }

        try:
            response = requests.get(self.NAVER_API_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_list = []
            for item in data.get("items", []):
                title = item.get("title", "").replace("<b>", "").replace("</b>", "").replace("&quot;", "\"")
                link = item.get("originallink") or item.get("link", "")
                description = item.get("description", "").replace("<b>", "").replace("</b>", "")
                pub_date_str = item.get("pubDate", "")

                # Parse Naver's pubDate format: "Mon, 26 Sep 2016 07:50:00 +0900"
                try:
                    published_at = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                except ValueError:
                    published_at = datetime.now()

                # Use description as initial summary
                news_list.append(News(
                    title=title, 
                    link=link, 
                    published_at=published_at,
                    summary=description
                ))
                
            return news_list

        except Exception as e:
            print(f"[ERROR] Failed to fetch news from Naver: {e}")
            return []
