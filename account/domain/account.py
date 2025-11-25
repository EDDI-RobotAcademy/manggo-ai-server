from datetime import datetime
from typing import Optional


class Account:
    def __init__(self, email: str, name: str):
        self.id: Optional[int] = None
        self.email = email
        self.name = name
        self.created_at: datetime = datetime.utcnow()
