from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Connexion requise.")

    user = db.get(User, user_id)
    if user is None or user.status != UserStatus.approved:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Connexion requise.")

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur.")
    return user
