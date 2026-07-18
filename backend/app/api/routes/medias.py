from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import Media
from app.models.media import MediaType
from app.schemas.media import MediaListResponse, MediaOut, MediaUpdate

router = APIRouter(tags=["medias"], dependencies=[Depends(get_current_user)])


@router.get("/medias", response_model=MediaListResponse)
def list_medias(
    type: Optional[MediaType] = Query(None),
    q: Optional[str] = Query(None, description="Recherche sur le nom de fichier"),
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    favori: Optional[bool] = Query(None),
    limit: int = Query(50, le=1000, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    effective_date = func.coalesce(Media.date_originale, Media.date_upload)
    stmt = select(Media)

    if type is not None:
        stmt = stmt.where(Media.type == type)
    if q:
        stmt = stmt.where(Media.filename.ilike(f"%{q}%"))
    if date_debut is not None:
        stmt = stmt.where(func.date(effective_date) >= date_debut)
    if date_fin is not None:
        stmt = stmt.where(func.date(effective_date) <= date_fin)
    if favori is not None:
        stmt = stmt.where(Media.favori == favori)

    total = db.scalar(select(func.count()).select_from(stmt.with_only_columns(Media.id).subquery()))

    stmt = stmt.order_by(effective_date.desc()).limit(limit).offset(offset)
    items = db.execute(stmt).scalars().all()

    return MediaListResponse(items=items, total=total or 0)


@router.patch("/medias/{media_id}", response_model=MediaOut)
def update_media(media_id: int, payload: MediaUpdate, db: Session = Depends(get_db)):
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Média introuvable.")

    if payload.favori is not None:
        media.favori = payload.favori

    if payload.filename is not None:
        filename = payload.filename.strip()
        if not filename:
            raise HTTPException(status_code=400, detail="Le nom ne peut pas être vide.")
        media.filename = filename

    db.commit()
    db.refresh(media)
    return media


@router.delete("/medias/{media_id}", status_code=204)
def delete_media(media_id: int, db: Session = Depends(get_db)):
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Média introuvable.")

    for relative_path in (media.chemin_stockage, media.vignette_path):
        if not relative_path:
            continue
        file_path = Path(settings.media_root) / relative_path
        file_path.unlink(missing_ok=True)

    db.delete(media)
    db.commit()
