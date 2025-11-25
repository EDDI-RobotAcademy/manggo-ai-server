import asyncio
import re

from transformers import pipeline

def deduplicate_sentences(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen = set()
    result = []
    for s in sentences:
        s_clean = s.strip()
        if s_clean and s_clean not in seen:
            seen.add(s_clean)
            result.append(s_clean)
    return " ".join(result)

# 텍스트 정제
def clean_text(text: str) -> str:
    text = re.sub(r'\d+', '', text)  # 숫자 제거
    # Latin/Test 문구 제거
    text = re.sub(
        r'Lorem ipsum|Vestibulum|Class aptent|Curabitur|Morbi|Fusce|Proin|Praesent|Nunc|Nulla|Etiam|Suspendisse|Aenean',
        '', text, flags=re.IGNORECASE
    )
    # 특수문자 제거 (영문+한글+기본 문장부호만 허용)
    text = re.sub(r'[^a-zA-Z0-9가-힣\s.,;?!]', '', text)
    # 연속 공백 제거
    return re.sub(r'\s+', ' ', text).strip()

# 문장 단위 청킹
def chunk_text(text: str, max_chars: int = 1000):
    text = clean_text(text)
    if not text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    seen_sentences = set()

    for s in sentences:
        s_clean = s.strip()
        if not s_clean or s_clean in seen_sentences:
            continue
        seen_sentences.add(s_clean)
        if len(current) + len(s_clean) + 1 <= max_chars:
            current += s_clean + " "
        else:
            if current:
                chunks.append(current.strip())
            current = s_clean + " "
    if current:
        chunks.append(current.strip())

    return chunks

# 모델 로드
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)
qa_model = pipeline("text2text-generation", model="google/flan-t5-large", device=-1)

# 안전한 모델 호출
async def run_summarize(text: str, max_len: int, min_len: int):
    return await asyncio.to_thread(
        lambda: summarizer(text, max_length=max_len, min_length=min_len, truncation=True)[0]["summary_text"]
    )

async def run_qa(prompt: str):
    return await asyncio.to_thread(
        lambda: qa_model(prompt, max_new_tokens=150)[0]["generated_text"]
    )

# 계층 요약
async def safe_summarizer(text: str, max_len: int, min_len: int):
    chunks = chunk_text(text, 1000)
    lvl1 = [await run_summarize(c, max_len, min_len) for c in chunks]
    combined = " ".join(lvl1)
    # 길면 2단계 요약
    if len(combined) > 2000:
        lvl2_chunks = chunk_text(combined, 1000)
        lvl2 = [await run_summarize(c, max_len, min_len) for c in lvl2_chunks]
        combined = " ".join(lvl2)
    return deduplicate_sentences(combined)

# 요약 타입
async def bullet_summarizer(text):   return await safe_summarizer(text, 180, 40)
async def abstract_summarizer(text): return await safe_summarizer(text, 250, 80)
async def casual_summarizer(text):   return await safe_summarizer(text, 180, 40)
async def consensus_summarizer(lst):
    joined = " ".join([s for s in lst if s])
    return await safe_summarizer(joined, 200, 60)

# QA
async def answer_agent(summary: str, question: str):
    prompt_template = f"""
Context:
{summary}

Question:
{question}

Answer strictly based on the context above. Do not hallucinate or repeat unrelated information.
Answer:"""
    chunks = chunk_text(prompt_template, 1000)
    answers = []
    for c in chunks:
        ans = await run_qa(c)
        ans_clean = deduplicate_sentences(re.sub(r'\s+', ' ', ans).strip())
        answers.append(ans_clean)
    # 청킹 단위 답변 중복 제거 후 합치기
    return " ".join(list(dict.fromkeys(answers)))