from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Categorie, Lien
from app.schemas.categorie import CategorieCount

router = APIRouter(tags=["categories"], dependencies=[Depends(get_current_user)])


@router.get("/categories", response_model=List[CategorieCount])
def list_categories(db: Session = Depends(get_db)):
    stmt = (
        select(Categorie, func.count(Lien.id).label("nombre_liens"))
        .outerjoin(Lien, Lien.categorie_id == Categorie.id)
        .group_by(Categorie.id)
        .order_by(Categorie.id)
    )
    rows = db.execute(stmt).all()
    return [
        CategorieCount(id=categorie.id, nom=categorie.nom, couleur=categorie.couleur, nombre_liens=nombre_liens)
        for categorie, nombre_liens in rows
    ]
