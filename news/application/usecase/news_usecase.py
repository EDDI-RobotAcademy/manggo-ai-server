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

from news.domain.article import Article

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

# ---------- usecase ----------
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
    def _parse_yyyy_mm_dd(self, s: str) -> date_type:
        return datetime.strptime(s, "%Y-%m-%d").date()

    def _day_range_kst(self, d: date_type):
        start = datetime.combine(d, time.min).replace(tzinfo=KST)
        end = start + timedelta(days=1)
        return start.replace(tzinfo=None), end.replace(tzinfo=None)

    def list_articles(
        self, db: Session,
        category: str | None, date: str | None, from_: str | None, to: str | None, q: str | None,
        page: int, size: int
    ) -> dict:
        filters = []
        if category:
            filters.append(Article.category == category)

        if date:
            d = self._parse_yyyy_mm_dd(date)
            start, end = self._day_range_kst(d)
            filters.append(and_(Article.published_at >= start, Article.published_at < end))
        else:
            if from_:
                d = self._parse_yyyy_mm_dd(from_)
                start, _ = self._day_range_kst(d)
                filters.append(Article.published_at >= start)
            if to:
                d = self._parse_yyyy_mm_dd(to)
                _, end = self._day_range_kst(d)
                filters.append(Article.published_at < end)

        if q:
            filters.append(Article.title.like(f"%{q}%"))

        where_clause = and_(*filters) if filters else None

        total_stmt = select(func.count()).select_from(Article)
        if where_clause is not None:
            total_stmt = total_stmt.where(where_clause)
        total = db.execute(total_stmt).scalar_one()

        stmt = select(Article).order_by(desc(Article.published_at)).offset((page - 1) * size).limit(size)
        if where_clause is not None:
            stmt = stmt.where(where_clause)

        rows = db.execute(stmt).scalars().all()

        return {
            "page": page,
            "size": size,
            "total": total,
            "items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "source": r.source,
                    "category": r.category,
                    "url": r.url,
                    "published_at": r.published_at.isoformat(),
                }
                for r in rows
            ],
        }

    def get_article(self, db: Session, article_id: int) -> dict:
        row = db.get(Article, article_id)
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return {
            "id": row.id,
            "title": row.title,
            "source": row.source,
            "category": row.category,
            "url": row.url,
            "published_at": row.published_at.isoformat(),
            "content": row.content,
        }
