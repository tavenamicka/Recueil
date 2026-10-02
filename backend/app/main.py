from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.categories import router as categories_router
from app.api.routes.import_ import router as import_router
from app.api.routes.liens import router as liens_router
from app.api.routes.medias import router as medias_router
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole, UserStatus

_is_prod = settings.environment == "production"
app = FastAPI(
    title=settings.app_name,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(import_router)
app.include_router(liens_router)
app.include_router(medias_router)
app.include_router(categories_router)

Path(settings.media_root).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_root), name="media")


@app.on_event("startup")
def seed_admin() -> None:
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.role == UserRole.admin).first()
        if existing_admin is None:
            admin = User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                role=UserRole.admin,
                status=UserStatus.approved,
                approved_at=datetime.now(timezone.utc),
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
