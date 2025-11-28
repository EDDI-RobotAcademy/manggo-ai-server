import json

import httpx
from bs4 import BeautifulSoup
import trafilatura

async def fetch_html(url:str)->str:
    timeout = httpx.Timeout(10.0, connect=5.0)
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text

def parse_article(url: str, html: str) -> tuple[str, str]:
    downloaded = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True
    )
    if downloaded:
        data = json.loads(downloaded)
        title = (data.get("title") or "").strip()
        text = (data.get("text") or "").strip()
        if title or text:
            return title, text

        soup = BeautifulSoup(html, "html.parser")
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        text = soup.get_text(separator="\n", strip=True)

    return title, text


async def run_crawling(url: str) -> tuple[str, str]:
    print(url)
    html = await fetch_html(url)
    title, contents = parse_article(url, html)
    return title, contents
