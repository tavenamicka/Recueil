from typing import Literal, Optional

from pydantic import BaseModel

from app.schemas.media import MediaOut

__all__ = ["ImportTxtStarted", "ImportStatus", "MediaOut"]


class ImportTxtStarted(BaseModel):
    job_id: str


class ImportStatus(BaseModel):
    status: Literal["processing", "done", "error"]
    current: int = 0
    total: int = 0
    nouveaux: int = 0
    doublons: int = 0
    echecs: int = 0
    message: Optional[str] = None
