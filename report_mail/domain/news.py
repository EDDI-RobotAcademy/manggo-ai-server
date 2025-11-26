from dataclasses import dataclass
from datetime import datetime

@dataclass
class News:
    title: str
    link: str
    published_at: datetime
    summary: str = ""
