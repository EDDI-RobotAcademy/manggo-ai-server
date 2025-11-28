from io import BytesIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from news.adapter.input.web.request.news_summary_request import NewsSummarizeRequest
from news.application.usecase.news_usecase import NewsUseCase

news_router = APIRouter(tags=["news"])
news_usecase = NewsUseCase()

# ✅ 한글 폰트 등록 (WSL/리눅스에서 보통 경로)
pdfmetrics.registerFont(TTFont("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"))

def make_pdf_bytes(title: str, body: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    c.setFont("NanumGothic", 14)
    c.drawString(40, height - 60, title)

    c.setFont("NanumGothic", 11)
    text = c.beginText(40, height - 90)
    text.setLeading(16)

    # 간단 줄바꿈(너무 길면 적당히 쪼개서 넣기)
    for line in body.split("\n"):
        # 한 줄이 너무 길면 약간 잘라서 넣는 간단 처리
        while len(line) > 90:
            text.textLine(line[:90])
            line = line[90:]
        text.textLine(line)

    c.drawText(text)
    c.showPage()
    c.save()
    return buf.getvalue()