from datetime import datetime

from pydantic import BaseModel


class SyncRunResponse(BaseModel):
    status: str
    started_at: datetime
    accounts: int
