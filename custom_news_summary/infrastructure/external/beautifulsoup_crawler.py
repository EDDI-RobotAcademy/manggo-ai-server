import requests
from bs4 import BeautifulSoup

from custom_news_summary.application.port.crawler_port import ContentCrawlerPort


class BeautifulSoupCrawler(ContentCrawlerPort):

    def crawl(self, url: str) -> str:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        return '\n'.join([p.get_text(strip=True) for p in paragraphs])