from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.throttle import throttle_login, record_login_failure, clear_login_failures
from app.db.session import get_db
from app.models.password_reset import PasswordResetRequest
from app.models.user import User, UserStatus
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, MessageResponse, RegisterRequest, UserOut
from app.services.email_service import send_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=201)
def register(payload: RegisterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not email or not payload.password:
        raise HTTPException(status_code=400, detail="Email et mot de passe requis.")

    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email.")

    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()

    background_tasks.add_task(
        send_email,
        settings.admin_email,
        "Recueil — nouvelle demande de compte",
        f"{email} demande un accès à Recueil. Valide ou refuse la demande depuis le panneau admin.",
    )

    return MessageResponse(
        message="Ta demande a été envoyée. Un administrateur doit valider ton compte avant que tu puisses te connecter."
    )


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    throttle_login(request)
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        record_login_failure(request)
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    if user.status == UserStatus.pending:
        raise HTTPException(status_code=403, detail="Ton compte est en attente de validation par l'administrateur.")
    if user.status == UserStatus.rejected:
        raise HTTPException(status_code=403, detail="Ta demande d'accès a été refusée.")

    clear_login_failures(request)
    request.session["user_id"] = user.id
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request):
    request.session.clear()
    return MessageResponse(message="Déconnecté.")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not payload.new_password:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe ne peut pas être vide.")

    user = db.query(User).filter(User.email == email).first()
    if user is not None and user.status == UserStatus.approved:
        reset = PasswordResetRequest(
            user_id=user.id,
            nouveau_mot_de_passe_hash=hash_password(payload.new_password),
        )
        db.add(reset)
        db.commit()

        background_tasks.add_task(
            send_email,
            settings.admin_email,
            "Recueil — demande de réinitialisation de mot de passe",
            f"{email} demande un nouveau mot de passe. Valide ou refuse la demande depuis le panneau admin.",
        )

    return MessageResponse(
        message="Si un compte existe avec cet email, ta demande a été transmise à l'administrateur pour validation."
    )
