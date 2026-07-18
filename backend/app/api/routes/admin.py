from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.password_reset import PasswordResetRequest
from app.models.user import User, UserStatus
from app.schemas.auth import MessageResponse, PasswordResetRequestOut, UserOut
from app.services.email_service import send_email

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/approve", response_model=UserOut)
def approve_user(user_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    user.status = UserStatus.approved
    user.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    background_tasks.add_task(
        send_email,
        user.email,
        "Recueil — accès approuvé",
        "Ton compte a été validé, tu peux maintenant te connecter à Recueil.",
    )
    return user


@router.post("/users/{user_id}/reject", response_model=UserOut)
def reject_user(user_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    user.status = UserStatus.rejected
    db.commit()
    db.refresh(user)

    background_tasks.add_task(
        send_email,
        user.email,
        "Recueil — demande d'accès refusée",
        "Ta demande d'accès à Recueil a été refusée par l'administrateur.",
    )
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Tu ne peux pas supprimer ton propre compte.")

    db.query(PasswordResetRequest).filter(PasswordResetRequest.user_id == user.id).delete()
    db.delete(user)
    db.commit()


@router.get("/password-resets", response_model=List[PasswordResetRequestOut])
def list_password_resets(db: Session = Depends(get_db)):
    stmt = (
        select(PasswordResetRequest)
        .options(joinedload(PasswordResetRequest.user))
        .order_by(PasswordResetRequest.created_at.desc())
    )
    resets = db.execute(stmt).unique().scalars().all()
    return [
        PasswordResetRequestOut(
            id=r.id,
            user_id=r.user_id,
            user_email=r.user.email,
            status=r.status,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
        )
        for r in resets
    ]


@router.post("/password-resets/{reset_id}/approve", response_model=MessageResponse)
def approve_password_reset(reset_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    reset = db.get(PasswordResetRequest, reset_id)
    if reset is None:
        raise HTTPException(status_code=404, detail="Demande introuvable.")

    user = db.get(User, reset.user_id)
    user.password_hash = reset.nouveau_mot_de_passe_hash
    reset.status = UserStatus.approved
    reset.resolved_at = datetime.now(timezone.utc)
    db.commit()

    background_tasks.add_task(
        send_email,
        user.email,
        "Recueil — mot de passe réinitialisé",
        "Ton nouveau mot de passe est actif, tu peux te connecter à Recueil avec.",
    )
    return MessageResponse(message="Nouveau mot de passe activé.")


@router.post("/password-resets/{reset_id}/reject", response_model=MessageResponse)
def reject_password_reset(reset_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    reset = db.get(PasswordResetRequest, reset_id)
    if reset is None:
        raise HTTPException(status_code=404, detail="Demande introuvable.")

    reset.status = UserStatus.rejected
    reset.resolved_at = datetime.now(timezone.utc)
    db.commit()

    user = db.get(User, reset.user_id)
    background_tasks.add_task(
        send_email,
        user.email,
        "Recueil — demande de réinitialisation refusée",
        "Ta demande de réinitialisation de mot de passe a été refusée par l'administrateur.",
    )
    return MessageResponse(message="Demande refusée.")
