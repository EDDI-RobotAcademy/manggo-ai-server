import os
import hashlib
import aiohttp

# 캐시 디렉토리 경로 설정
CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_filename(doc_url: str) -> str:
    file_hash = hashlib.sha256(doc_url.encode()).hexdigest()
    file_path = os.path.join(CACHE_DIR, f"{file_hash}.pdf")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return file_path

async def download_document(doc_url: str) -> bytes:
    cache_path = get_cache_filename(doc_url)

    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f.read()

    async with aiohttp.ClientSession() as session:
        async with session.get(doc_url) as resp:
            if resp.status != 200:
                raise Exception(f"다운로드 실패: {resp.status}")
            content = await resp.read()

    with open(cache_path, "wb") as f:
        f.write(content)

    return content