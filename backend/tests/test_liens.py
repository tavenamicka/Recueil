import io
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from app.core.config import settings
from app.models import Categorie


def test_list_liens_returns_seeded_lien(admin_client, lien):
    resp = admin_client.get("/liens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["url"] == lien.url


def test_list_liens_filter_by_categorie(admin_client, lien, db_session):
    autre = Categorie(nom="Autre", couleur="#4B5563")
    db_session.add(autre)
    db_session.commit()

    resp_empty = admin_client.get(f"/liens?categorie_id={autre.id}")
    assert resp_empty.json()["total"] == 0

    resp_match = admin_client.get(f"/liens?categorie_id={lien.categorie_id}")
    assert resp_match.json()["total"] == 1


def test_list_liens_search(admin_client, lien):
    resp_empty = admin_client.get("/liens?q=inexistant-xyz")
    assert resp_empty.json()["total"] == 0

    resp_match = admin_client.get("/liens?q=Titre")
    assert resp_match.json()["total"] == 1


def test_list_liens_date_range(admin_client, lien):
    resp_future = admin_client.get("/liens?date_debut=2030-01-01")
    assert resp_future.json()["total"] == 0

    resp_past = admin_client.get("/liens?date_debut=2025-01-01")
    assert resp_past.json()["total"] == 1


def test_list_liens_favori_filter(admin_client, lien):
    resp_before = admin_client.get("/liens?favori=true")
    assert resp_before.json()["total"] == 0

    admin_client.patch(f"/liens/{lien.id}", json={"favori": True})

    resp_after = admin_client.get("/liens?favori=true")
    assert resp_after.json()["total"] == 1


def test_update_lien_categorie(admin_client, lien, db_session):
    autre = Categorie(nom="Business / Marketing / Carrière", couleur="#0A66C2")
    db_session.add(autre)
    db_session.commit()

    resp = admin_client.patch(f"/liens/{lien.id}", json={"categorie_id": autre.id})
    assert resp.status_code == 200
    assert resp.json()["categorie"]["id"] == autre.id


def test_update_lien_with_unknown_categorie_rejected(admin_client, lien):
    resp = admin_client.patch(f"/liens/{lien.id}", json={"categorie_id": 999999})
    assert resp.status_code == 400


def test_update_lien_titre(admin_client, lien):
    resp = admin_client.patch(f"/liens/{lien.id}", json={"titre_page": "Nouveau titre"})
    assert resp.status_code == 200
    assert resp.json()["titre_page"] == "Nouveau titre"


def test_update_lien_titre_empty_rejected(admin_client, lien):
    resp = admin_client.patch(f"/liens/{lien.id}", json={"titre_page": "   "})
    assert resp.status_code == 400


def test_update_lien_not_found(admin_client):
    resp = admin_client.patch("/liens/999999", json={"favori": True})
    assert resp.status_code == 404


def test_delete_lien(admin_client, lien):
    resp = admin_client.delete(f"/liens/{lien.id}")
    assert resp.status_code == 204
    assert admin_client.get("/liens").json()["total"] == 0


def test_delete_lien_removes_vignette_file(admin_client, lien, db_session, _fresh_media_dir):
    vignette_dir = Path(settings.media_root) / "vignettes"
    vignette_dir.mkdir(parents=True, exist_ok=True)
    vignette_file = vignette_dir / "test.jpg"
    vignette_file.write_bytes(b"fake")
    lien.vignette_path = "vignettes/test.jpg"
    db_session.add(lien)
    db_session.commit()

    resp = admin_client.delete(f"/liens/{lien.id}")
    assert resp.status_code == 204
    assert not vignette_file.exists()


def test_delete_lien_not_found(admin_client):
    resp = admin_client.delete("/liens/999999")
    assert resp.status_code == 404


@patch("app.services.whatsapp_link_extractor.requests.get")
def test_create_lien_success(mock_get, admin_client):
    mock_get.return_value = Mock(
        text='<html><head><meta property="og:title" content="Un super article"></head></html>'
    )
    resp = admin_client.post("/liens", json={"url": "https://www.korben.info/un-article"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["url"] == "https://www.korben.info/un-article"
    assert data["domaine"] == "korben.info"
    assert data["titre_page"] == "Un super article"
    assert data["categorie"]["nom"] == "Technologie / IA"

    liens = admin_client.get("/liens").json()
    assert liens["total"] == 1


@patch("app.services.whatsapp_link_extractor.requests.get")
def test_create_lien_with_og_image_downloads_thumbnail(mock_get, admin_client, _fresh_media_dir):
    # whatsapp_link_extractor.py et media_service.py font tous deux `import requests` :
    # c'est le même module partagé (sys.modules), donc un seul patch suffit et doit
    # distinguer les deux appels (page HTML vs octets de l'image) par l'URL demandée.
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="green").save(buf, format="JPEG")
    html_response = Mock(
        text='<html><head>'
        '<meta property="og:title" content="Un article avec image">'
        '<meta property="og:image" content="https://example.com/photo.jpg">'
        "</head></html>"
    )
    image_response = Mock(content=buf.getvalue())
    image_response.raise_for_status = Mock()

    def fake_get(url, *args, **kwargs):
        return image_response if url == "https://example.com/photo.jpg" else html_response

    mock_get.side_effect = fake_get

    resp = admin_client.post("/liens", json={"url": "https://www.exemple-photo.tld/un-article"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["vignette_path"] is not None
    assert data["vignette_path"].startswith("vignettes/")
    assert (Path(settings.media_root) / data["vignette_path"]).exists()


@patch("app.services.whatsapp_link_extractor.requests.get")
def test_create_lien_duplicate_rejected(mock_get, admin_client):
    mock_get.return_value = Mock(text="<html></html>")
    payload = {"url": "https://example.com/dedup-manual"}

    resp1 = admin_client.post("/liens", json=payload)
    assert resp1.status_code == 201

    resp2 = admin_client.post("/liens", json=payload)
    assert resp2.status_code == 409


def test_create_lien_invalid_url_rejected(admin_client):
    resp = admin_client.post("/liens", json={"url": "pas-une-url"})
    assert resp.status_code == 400


def test_create_lien_requires_auth(client):
    resp = client.post("/liens", json={"url": "https://example.com/x"})
    assert resp.status_code == 401
