import html
from datetime import datetime
from pathlib import Path
from threading import Lock

from app.db.session import SessionLocal
from app.models import Categorie, Lien
from app.services.whatsapp_link_extractor import categorize, fetch_title, parse_export

_jobs: dict[str, dict] = {}
_jobs_lock = Lock()


def _set_job(job_id: str, **fields) -> None:
    with _jobs_lock:
        _jobs[job_id] = {**_jobs.get(job_id, {}), **fields}


def get_job(job_id: str) -> dict | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def get_or_create_categorie(db, nom: str) -> Categorie:
    categorie = db.query(Categorie).filter(Categorie.nom == nom).first()
    if categorie is None:
        categorie = Categorie(nom=nom, couleur="#4B5563")
        db.add(categorie)
        db.flush()
    return categorie


def run_txt_import(job_id: str, tmp_path: Path) -> None:
    db = SessionLocal()
    try:
        records = parse_export(tmp_path)
        total = len(records)
        nouveaux = doublons = echecs = 0
        _set_job(job_id, status="processing", current=0, total=total, nouveaux=0, doublons=0, echecs=0)

        for i, r in enumerate(records, start=1):
            if db.query(Lien).filter(Lien.url == r["url"]).first():
                doublons += 1
            else:
                titre_page = r["title_brut"] or fetch_title(r["url"])
                if not titre_page:
                    echecs += 1
                # certains sites renvoient déjà des entités HTML dans og:title (ex: &#39;)
                titre_page = html.unescape(titre_page) if titre_page else titre_page
                categorie = get_or_create_categorie(
                    db, categorize(r["domain"], titre_page or r["title_brut"])
                )
                db.add(
                    Lien(
                        url=r["url"],
                        date=datetime.strptime(r["date"], "%d/%m/%Y").date(),
                        heure=datetime.strptime(r["time"], "%H:%M").time(),
                        domaine=r["domain"],
                        titre_brut=r["title_brut"],
                        titre_page=titre_page,
                        categorie_id=categorie.id,
                    )
                )
                db.flush()
                nouveaux += 1

            _set_job(job_id, current=i, nouveaux=nouveaux, doublons=doublons, echecs=echecs)

        db.commit()
        _set_job(
            job_id,
            status="done",
            message=f"{nouveaux} nouveaux liens classés, {doublons} doublons ignorés, {echecs} échecs d'enrichissement",
        )
    except Exception as exc:
        db.rollback()
        _set_job(job_id, status="error", message=str(exc))
    finally:
        db.close()
        tmp_path.unlink(missing_ok=True)
