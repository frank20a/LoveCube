from uuid import uuid4
from datetime import datetime, timedelta


class SessionKey:
    def __init__(self, user_id, name, email):
        self.user = user_id
        self.name = name
        self.email = email
        self.expiry = datetime.utcnow() + timedelta(days=30)
