from datetime import date as date_, datetime, time as time_
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CategorieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    couleur: str


class LienOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    date: Optional[date_] = None
    heure: Optional[time_] = None
    domaine: Optional[str] = None
    titre_brut: Optional[str] = None
    titre_page: Optional[str] = None
    date_ajout: datetime
    favori: bool
    categorie: Optional[CategorieOut] = None


class LienListResponse(BaseModel):
    items: List[LienOut]
    total: int


class LienUpdate(BaseModel):
    categorie_id: Optional[int] = None
    favori: Optional[bool] = None
    titre_page: Optional[str] = None


class LienCreate(BaseModel):
    url: str
