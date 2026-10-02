"""Configuration pytest pour les tests d'endpoints.

Bascule sur une base Postgres de test dédiée (recueil_test, créée si besoin)
et un répertoire média jetable, pour ne jamais toucher aux vraies données.
Nécessite un accès réseau à "db" : lancer via
`docker compose exec backend pytest`, pas un `docker run` isolé du réseau.
"""

import os
import shutil
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
from sqlalchemy import create_engine, text

TEST_DB_NAME = "recueil_test"
TEST_MEDIA_ROOT = "/tmp/recueil-test-media"


def _with_db_name(url: str, db_name: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{db_name}", parts.query, parts.fragment))


def _ensure_test_database_exists(source_url: str, db_name: str) -> None:
    admin_engine = create_engine(source_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()


_source_database_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://recueil:recueil@db:5432/recueil")
_ensure_test_database_exists(_source_database_url, TEST_DB_NAME)

os.environ["DATABASE_URL"] = _with_db_name(_source_database_url, TEST_DB_NAME)
os.environ["MEDIA_ROOT"] = TEST_MEDIA_ROOT
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_EMAIL"] = "admin@test.local"
os.environ["ADMIN_PASSWORD"] = "test-admin-password"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Categorie, Lien  # noqa: E402

ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


@pytest.fixture
def _fresh_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def _fresh_media_dir():
    media_root = Path(os.environ["MEDIA_ROOT"])
    shutil.rmtree(media_root, ignore_errors=True)
    media_root.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(media_root, ignore_errors=True)


@pytest.fixture
def db_session(_fresh_database):
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def _fresh_login_throttle():
    """Le throttle de connexion (app/core/throttle.py) vit dans un dict au
    niveau module : sans remise à zéro, les échecs d'un test s'additionnent
    à ceux du suivant (même IP `testclient` pour tout TestClient) jusqu'à
    déclencher un 429 inattendu bien avant la limite réelle de 10."""
    from app.core.throttle import _reset_all

    _reset_all()
    yield
    _reset_all()


@pytest.fixture
def client(_fresh_database, _fresh_media_dir):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_client(client):
    resp = client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200
    return client


@pytest.fixture
def categorie(db_session):
    c = Categorie(nom="Technologie / IA", couleur="#1F4E78")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture
def lien(db_session, categorie):
    from datetime import date, time

    l = Lien(
        url="https://example.com/test-article",
        date=date(2026, 1, 1),
        heure=time(10, 0),
        domaine="example.com",
        titre_brut="Titre brut",
        titre_page="Titre de test",
        categorie_id=categorie.id,
    )
    db_session.add(l)
    db_session.commit()
    db_session.refresh(l)
    return l


def approve_by_email(client, email):
    """Bascule client sur la session admin, approuve le compte donné, sans changer l'état si déjà admin."""
    client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    users = client.get("/admin/users").json()
    target = next(u for u in users if u["email"] == email)
    client.post(f"/admin/users/{target['id']}/approve")
    return target
