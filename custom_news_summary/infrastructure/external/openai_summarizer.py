import os

from openai import OpenAI

from custom_news_summary.application.port.summarizer_port import TextSummarizerPort


class OpenAISummarizer(TextSummarizerPort):

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)

    def summarize(self, content: str) -> tuple[str, str]:
        # 요약 생성
        summary_response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "뉴스 기사를 간결하게 요약해주세요."},
                {"role": "user", "content": content}
            ]
        )

        summary_text = summary_response.choices[0].message.content

        # 제목 생성
        title_response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "요약문에 맞는 짧은 제목을 생성하세요."},
                {"role": "user", "content": summary_text}
            ]
        )

        title = title_response.choices[0].message.content.strip()

        return title, summary_text