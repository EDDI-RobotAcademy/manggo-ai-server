from datetime import datetime
from typing import List
from report_mail.application.port.news_provider_port import NewsProviderPort
from report_mail.application.port.summarizer_port import SummarizerPort
from report_mail.application.port.mail_sender_port import MailSenderPort

class SendDailyReportMailUseCase:
    def __init__(
        self,
        news_provider: NewsProviderPort,
        summarizer: SummarizerPort,
        mail_sender: MailSenderPort
    ):
        self.news_provider = news_provider
        self.summarizer = summarizer
        self.mail_sender = mail_sender

    def execute(self, to_email: str):
        print(f"[INFO] Starting daily report for {to_email}")
        
        # 1. Fetch News
        all_news = self.news_provider.get_major_news()
        if not all_news:
            print("[WARN] No news found.")
            return

        # 2. Filter top 5
        target_news = all_news[:5]

        # 3. Summarize & Format
        mail_content_html = f"<h1>Daily News Report ({datetime.now().strftime('%Y-%m-%d')})</h1><hr>"
        for news in target_news:

            text_to_summarize = f"{news.title}. {news.summary}"
            summary = self.summarizer.summarize(text_to_summarize)
            
            mail_content_html += f"""
            <div style="margin-bottom: 20px;">
                <h3><a href="{news.link}">{news.title}</a></h3>
                <p style="font-size: 14px; color: #555;">{summary}</p>
            </div>
            """

        mail_content_html += "<hr><p>End of Report</p>"

        # 4. Send Mail
        self.mail_sender.send_mail(
            to=to_email,
            subject=f"Daily News Report - {datetime.now().strftime('%Y-%m-%d')}",
            content=mail_content_html
        )
        print("[INFO] Daily report finished.")
