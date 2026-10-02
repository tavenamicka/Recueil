import html
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import Categorie, Lien
from app.schemas.lien import LienCreate, LienListResponse, LienOut, LienUpdate
from app.services.import_service import get_or_create_categorie
from app.services.media_service import download_lien_thumbnail
from app.services.whatsapp_link_extractor import categorize, fetch_og_image, fetch_title

router = APIRouter(tags=["liens"], dependencies=[Depends(get_current_user)])


@router.post("/liens", response_model=LienOut, status_code=201)
def create_lien(payload: LienCreate, db: Session = Depends(get_db)):
    url = payload.url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(
            status_code=400,
            detail="Lien invalide. Colle une URL complète, ex: https://exemple.com/page.",
        )

    if db.query(Lien).filter(Lien.url == url).first():
        raise HTTPException(status_code=409, detail="Ce lien est déjà dans le recueil.")

    domaine = parsed.netloc.replace("www.", "")
    titre_page = fetch_title(url)
    titre_page = html.unescape(titre_page) if titre_page else None
    categorie = get_or_create_categorie(db, categorize(domaine, titre_page or ""))
    image_url = fetch_og_image(url)
    vignette_path = download_lien_thumbnail(image_url) if image_url else None

    now = datetime.now()
    lien = Lien(
        url=url,
        date=now.date(),
        heure=now.time(),
        domaine=domaine,
        titre_page=titre_page,
        categorie_id=categorie.id,
        vignette_path=vignette_path,
    )
    db.add(lien)
    db.commit()
    db.refresh(lien)
    return lien


@router.get("/liens", response_model=LienListResponse)
def list_liens(
    categorie_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, description="Recherche sur le titre, le domaine ou la catégorie"),
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    favori: Optional[bool] = Query(None),
    limit: int = Query(50, le=1000, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Lien).outerjoin(Categorie).options(joinedload(Lien.categorie))

    if categorie_id is not None:
        stmt = stmt.where(Lien.categorie_id == categorie_id)
    if date_debut is not None:
        stmt = stmt.where(Lien.date >= date_debut)
    if date_fin is not None:
        stmt = stmt.where(Lien.date <= date_fin)
    if favori is not None:
        stmt = stmt.where(Lien.favori == favori)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Lien.titre_page.ilike(pattern),
                Lien.titre_brut.ilike(pattern),
                Lien.domaine.ilike(pattern),
                Categorie.nom.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.with_only_columns(Lien.id).subquery()))

    stmt = stmt.order_by(Lien.date.desc().nullslast(), Lien.heure.desc().nullslast()).limit(limit).offset(offset)
    items = db.execute(stmt).unique().scalars().all()

    return LienListResponse(items=items, total=total or 0)


@router.patch("/liens/{lien_id}", response_model=LienOut)
def update_lien(lien_id: int, payload: LienUpdate, db: Session = Depends(get_db)):
    lien = db.get(Lien, lien_id)
    if lien is None:
        raise HTTPException(status_code=404, detail="Lien introuvable.")

    if payload.categorie_id is not None:
        categorie = db.get(Categorie, payload.categorie_id)
        if categorie is None:
            raise HTTPException(status_code=400, detail="Catégorie introuvable.")
        lien.categorie_id = payload.categorie_id

    if payload.favori is not None:
        lien.favori = payload.favori

    if payload.titre_page is not None:
        titre = payload.titre_page.strip()
        if not titre:
            raise HTTPException(status_code=400, detail="Le titre ne peut pas être vide.")
        lien.titre_page = titre

    db.commit()
    db.refresh(lien)
    return lien


@router.delete("/liens/{lien_id}", status_code=204)
def delete_lien(lien_id: int, db: Session = Depends(get_db)):
    lien = db.get(Lien, lien_id)
    if lien is None:
        raise HTTPException(status_code=404, detail="Lien introuvable.")

    if lien.vignette_path:
        (Path(settings.media_root) / lien.vignette_path).unlink(missing_ok=True)

    db.delete(lien)
    db.commit()
