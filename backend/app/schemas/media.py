from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.media import MediaType


class MediaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    type: MediaType
    chemin_stockage: str
    vignette_path: Optional[str] = None
    date_originale: Optional[datetime] = None
    date_upload: datetime
    taille_octets: int
    favori: bool
    duree_secondes: Optional[int] = None


class MediaListResponse(BaseModel):
    items: List[MediaOut]
    total: int


class MediaUpdate(BaseModel):
    favori: Optional[bool] = None
    filename: Optional[str] = None
