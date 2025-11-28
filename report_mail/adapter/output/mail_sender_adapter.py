import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from report_mail.application.port.mail_sender_port import MailSenderPort

class MailSenderAdapter(MailSenderPort):
    def send_mail(self, to: str, subject: str, content: str) -> None:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not smtp_user or not smtp_password:
            print("[ERROR] SMTP credentials not set.")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(content, "html"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            print(f"[INFO] Mail sent to {to}")
        except Exception as e:
            print(f"[ERROR] Failed to send mail: {e}")
