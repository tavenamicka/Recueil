"""Backfill ponctuel : télécharge une vignette (og:image) pour les liens déjà en base
qui n'en ont pas encore — c'est-à-dire tous ceux ajoutés avant l'introduction de cette
fonctionnalité. Best-effort : certains liens (posts Facebook Reels supprimés depuis,
contenu protégé...) resteront sans vignette, comme à l'import normal.

Usage :
    docker compose exec backend python -m app.scripts.backfill_lien_thumbnails
"""
from app.db.session import SessionLocal
from app.models import Lien
from app.services.media_service import download_lien_thumbnail
from app.services.whatsapp_link_extractor import fetch_og_image


def run() -> None:
    db = SessionLocal()
    try:
        liens = db.query(Lien).filter(Lien.vignette_path.is_(None)).order_by(Lien.id).all()
        total = len(liens)
        reussis = 0
        for i, lien in enumerate(liens, start=1):
            image_url = fetch_og_image(lien.url)
            vignette_path = download_lien_thumbnail(image_url) if image_url else None
            if vignette_path:
                lien.vignette_path = vignette_path
                reussis += 1
                db.commit()
            print(f"[{i}/{total}] {'OK' if vignette_path else '--'}  {lien.url}")
        print(f"\n{reussis}/{total} vignettes récupérées.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
