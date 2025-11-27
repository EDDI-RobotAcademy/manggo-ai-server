from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os

from report_mail.adapter.output.news_provider_from_naver_adapter import NewsProviderFromNaverAdapter
from report_mail.adapter.output.summarizer_adapter import OpenAISummarizerAdapter
from report_mail.adapter.output.mail_sender_adapter import MailSenderAdapter
from report_mail.application.usecase.send_daily_report_mail_usecase import SendDailyReportMailUseCase

def job_send_daily_mail():
    # Dependency Injection
    news_provider = NewsProviderFromNaverAdapter()
    summarizer = OpenAISummarizerAdapter()
    mail_sender = MailSenderAdapter()
    
    usecase = SendDailyReportMailUseCase(news_provider, summarizer, mail_sender)
    
    # Target email (could be from DB or env)
    target_email = os.getenv("REPORT_RECEIVE_EMAIL", "admin@example.com")
    usecase.execute(target_email)

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Schedule to run every day at 08:00 AM
    trigger = CronTrigger(hour=8, minute=0)
    
    scheduler.add_job(
        job_send_daily_mail,
        trigger=trigger,
        id="daily_news_report",
        name="Send Daily News Report",
        replace_existing=True
    )
    
    scheduler.start()
    print("[INFO] Scheduler started. Daily report scheduled for 08:00 AM.")
