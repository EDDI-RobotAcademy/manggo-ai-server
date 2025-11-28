from openai import OpenAI
from report_mail.application.port.summarizer_port import SummarizerPort
import os

class OpenAISummarizerAdapter(SummarizerPort):
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def summarize(self, text: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", # Using a capable model
                messages=[
                    {"role": "system", "content": "You are a helpful news summarizer."},
                    {"role": "user", "content": f"Summarize the following news article in 3-5 sentences in Korean:\n\n{text}"}
                ],
                max_tokens=300,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] Summarization failed: {e}")
            return "요약 실패"
