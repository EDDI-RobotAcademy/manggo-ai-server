from __future__ import annotations
from datetime import datetime, timedelta, time, date as date_type
from zoneinfo import ZoneInfo
from typing import List, Optional
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

import json, re

from fastapi import HTTPException
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc

from news.infrastructure.repository.news_repository import NewsRepository
from news.infrastructure.orm.summary_history_orm import SummaryHistoryORM
from news.infrastructure.orm.publisher_orm import PublisherORM
from news.infrastructure.orm.news_article_orm import NewsArticleORM
from weather.infrastructure.orm.news_category_orm import NewsCategoryORM

ARTICLE_SUMMARY_TYPE = "ARTICLE"
MODEL = NewsArticleORM
KST = ZoneInfo("Asia/Seoul")

# ---------- helpers ----------
def clean_news_text(text: str) -> str:
    t = re.sub(r"\r\n?", "\n", text or "")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    t = re.sub(r"(무단\s*전재\s*및\s*재배포\s*금지).*$", "", t, flags=re.IGNORECASE | re.DOTALL).strip()
    return t

def chunk_text(text: str, chunk_size: int = 3500, overlap: int = 300) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, cur = [], ""

    for p in paragraphs:
        if len(cur) + len(p) + 1 <= chunk_size:
            cur = (cur + "\n" + p).strip() if cur else p
        else:
            if cur:
                chunks.append(cur)
            cur = p

    if cur:
        chunks.append(cur)

    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, ch in enumerate(chunks):
            if i == 0:
                overlapped.append(ch)
                continue
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append((prev_tail + "\n" + ch).strip())
        chunks = overlapped

    return chunks

def make_pdf_bytes(title: str, body: str) -> bytes:
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("HYSMyeongJo-Medium", 16)
    c.drawString(40, h - 60, title)

    c.setFont("HYSMyeongJo-Medium", 11)
    t = c.beginText(40, h - 90)
    t.setLeading(16)

    for line in (body or "").splitlines():
        line = line.rstrip()
        if not line:
            t.textLine("")
            continue
        while len(line) > 60:
            t.textLine(line[:60])
            line = line[60:]
        t.textLine(line)

    c.drawText(t)
    c.showPage()
    c.save()
    return buf.getvalue()

class NewsUseCase:
    def __init__(self):
        self.client = AsyncOpenAI()

    async def _ask_gpt(self, model: str, prompt: str, max_tokens: int, temperature: float = 0.0) -> str:
        try:
            resp = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI call failed: {type(e).__name__}: {str(e)}")

    async def summarize_news(self, text: str) -> dict:
        cleaned = re.sub(r"\s+", " ", (text or "")).strip()
        if not cleaned:
            return {"summary": ""}

        prompt = f"다음 뉴스 핵심을 5줄로 요약해줘:\n\n{cleaned}"
        summary = await self._ask_gpt(model="gpt-4.1", prompt=prompt, max_tokens=400, temperature=0)
        return {"summary": summary}

    async def summarize_news_chunks(self, model: str, chunks: List[str], max_bullets: int) -> str:
        partial_summaries = []
        for idx, chunk in enumerate(chunks):
            prompt = f"""
너는 뉴스 요약 에이전트다.
다음은 뉴스 기사 일부다. 사실 중심으로 핵심만 간결하게 요약해라.
- 과장/추론 금지, 기사에 있는 내용만.
- 숫자/날짜/고유명사(인물, 기관, 장소)는 가능하면 보존.

[기사 일부 {idx+1}/{len(chunks)}]
{chunk}

[출력]
- 3~5줄 요약(문장형)
"""
            s = await self._ask_gpt(model=model, prompt=prompt, max_tokens=320, temperature=0)
            partial_summaries.append(s)

        merged = "\n".join(partial_summaries)
        final_prompt = f"""
너는 뉴스 통합 요약 에이전트다.
아래는 부분 요약들을 합친 내용이다. 중복을 제거하고 핵심만 남겨 통합 요약해라.

[부분 요약들]
{merged}

[출력 형식]
1) 한 문단 요약(3~5문장)
2) 핵심 불릿 {max_bullets}개 (각 1문장, 사실 중심)
3) 키워드 8개 (쉼표로 구분)
"""
        return await self._ask_gpt(model=model, prompt=final_prompt, max_tokens=600, temperature=0)

    async def qa_on_summary(self, model: str, summary: str, question: str) -> str:
        prompt = f"""
다음은 뉴스 요약이다. 요약에 포함된 정보만 사용해 질문에 답해라.
- 추론/상상 금지
- 요약에 근거가 없으면: "문서에 해당 정보 없음"

[요약]
{summary}

[질문]
{question}

[답변]
"""
        return await self._ask_gpt(model=model, prompt=prompt, max_tokens=250, temperature=0)

    async def analyze_opinions(self, model: str, summary: str) -> dict:
        prompt = f"""
반드시 JSON만 출력해라. 다른 텍스트 절대 금지.

[요약]
{summary}

[JSON 출력 형식]
{{
  "sentiment": "positive | negative | neutral",
  "key_points": ["...", "...", "...", "...", "..."]
}}
"""
        raw = await self._ask_gpt(model=model, prompt=prompt, max_tokens=250, temperature=0)
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not m:
            return {"sentiment": "unknown", "key_points": []}
        try:
            return json.loads(m.group(0))
        except Exception:
            return {"sentiment": "unknown", "key_points": []}

    async def analyze(self, text: str, question: Optional[str], max_bullets: int, model: str) -> dict:
        if not (text or "").strip():
            raise HTTPException(status_code=400, detail="Empty text")

        cleaned = clean_news_text(text)
        if not cleaned:
            raise HTTPException(status_code=400, detail="No usable text after cleaning")

        chunks = chunk_text(cleaned)
        if not chunks:
            raise HTTPException(status_code=500, detail="Chunking failed")

        summary = await self.summarize_news_chunks(model=model, chunks=chunks, max_bullets=max_bullets)

        answer = None
        if question and question.strip():
            answer = await self.qa_on_summary(model=model, summary=summary, question=question.strip())

        analysis = await self.analyze_opinions(model=model, summary=summary)

        return {
            "cleaned_text": cleaned,
            "chunk_count": len(chunks),
            "summary": summary,
            "answer": answer,
            "analysis": analysis,
        }

    # ---------- DB ----------
    def __init__(self):
        self.repo = NewsRepository()

    def list_articles(self, db: Session, page: int, size: int, category_id: int | None = None):
        return self.repo.list_articles(db=db, page=page, size=size, category_id=category_id)

    def get_article_detail(self, db: Session, article_id: int):
        data = self.repo.get_article_detail(db=db, article_id=article_id)
        if not data:
            raise HTTPException(status_code=404, detail="Article not found")
        return data        }