from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import asyncio  # (안 써도 되지만 구성 유지)
import json
import re
from typing import List, Optional

app = FastAPI()
client = AsyncOpenAI()


class NewsTextAnalyzeRequest(BaseModel):
    text: str = Field(..., description="뉴스 원문 텍스트")
    question: Optional[str] = Field(None, description="요약 기반으로 답할 질문(선택)")
    max_summary_bullets: int = Field(6, ge=3, le=12, description="요약 불릿 개수(3~12)")
    model: str = Field("gpt-4.1", description="사용 모델명")


class NewsUseCase:
    def __init__(self):
        self.client = AsyncOpenAI()

    async def summarize_news(self, text: str) -> dict:
        cleaned = re.sub(r"\s+", " ", (text or "")).strip()
        if not cleaned:
            return {"summary": ""}

        resp = await self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": f"다음 뉴스 핵심을 5줄로 요약해줘:\n\n{cleaned}"}],
            max_tokens=400,
            temperature=0,
        )
        return {"summary": resp.choices[0].message.content.strip()}


def clean_news_text(text: str) -> str:
    t = re.sub(r"\r\n?", "\n", text)
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


async def ask_gpt(model: str, prompt: str, max_tokens: int = 500, temperature: float = 0.0) -> str:
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # OpenAI 쪽 에러를 FastAPI에서 보기 쉽게 올려줌
        raise HTTPException(status_code=502, detail=f"OpenAI call failed: {type(e).__name__}: {str(e)}")


async def summarize_news(model: str, chunks: List[str], max_bullets: int) -> str:
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
        s = await ask_gpt(model=model, prompt=prompt, max_tokens=320)
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
    return await ask_gpt(model=model, prompt=final_prompt, max_tokens=600)


async def qa_on_summary(model: str, summary: str, question: str) -> str:
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
    return await ask_gpt(model=model, prompt=prompt, max_tokens=250)


async def analyze_opinions(model: str, summary: str) -> dict:
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
    raw = await ask_gpt(model=model, prompt=prompt, max_tokens=250)

    # ✅ 모델이 JSON 앞뒤에 텍스트 섞어도 JSON만 추출해서 파싱
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not m:
        return {"sentiment": "unknown", "key_points": []}

    try:
        return json.loads(m.group(0))
    except Exception:
        return {"sentiment": "unknown", "key_points": []}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
