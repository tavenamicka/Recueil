import io
import os
import subprocess
import tempfile

from PIL import Image

from app.core.config import settings


def _make_test_image_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="blue").save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def _make_test_audio_bytes(duration_seconds=3):
    with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
        subprocess.run(
            ["ffmpeg", "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration_seconds}", "-y", tmp.name],
            capture_output=True,
            check=True,
        )
        tmp.seek(0)
        return tmp.read()


def test_import_media_image_creates_thumbnail(admin_client):
    content = _make_test_image_bytes()
    resp = admin_client.post("/import/media", files={"file": ("photo.jpg", content, "image/jpeg")})
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "image"
    assert data["vignette_path"] is not None
    assert data["favori"] is False


def test_import_media_audio_extracts_duration(admin_client):
    content = _make_test_audio_bytes(3)
    resp = admin_client.post("/import/media", files={"file": ("clip.mp3", content, "audio/mpeg")})
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "audio"
    assert data["duree_secondes"] == 3
    assert data["vignette_path"] is None


def test_import_media_image_has_no_duration(admin_client):
    content = _make_test_image_bytes()
    resp = admin_client.post("/import/media", files={"file": ("photo.jpg", content, "image/jpeg")})
    assert resp.json()["duree_secondes"] is None


def test_import_media_unsupported_extension_rejected(admin_client):
    resp = admin_client.post("/import/media", files={"file": ("clip.heic", b"dummy", "image/heic")})
    assert resp.status_code == 400
    assert ".heic" in resp.json()["detail"]


def test_import_media_whatsapp_filename_date_extracted(admin_client):
    content = _make_test_image_bytes()
    resp = admin_client.post(
        "/import/media", files={"file": ("IMG-20260301-WA0000.jpg", content, "image/jpeg")}
    )
    data = resp.json()
    assert data["date_originale"].startswith("2026-03-01")


def test_import_media_requires_auth(client):
    content = _make_test_image_bytes()
    resp = client.post("/import/media", files={"file": ("photo.jpg", content, "image/jpeg")})
    assert resp.status_code == 401


def test_list_medias_filter_by_type(admin_client):
    content = _make_test_image_bytes()
    admin_client.post("/import/media", files={"file": ("a.jpg", content, "image/jpeg")})

    resp_image = admin_client.get("/medias?type=image")
    assert resp_image.json()["total"] == 1
    resp_video = admin_client.get("/medias?type=video")
    assert resp_video.json()["total"] == 0


def test_update_media_favori(admin_client):
    content = _make_test_image_bytes()
    created = admin_client.post("/import/media", files={"file": ("a.jpg", content, "image/jpeg")}).json()

    resp = admin_client.patch(f"/medias/{created['id']}", json={"favori": True})
    assert resp.status_code == 200
    assert resp.json()["favori"] is True


def test_update_media_filename(admin_client):
    content = _make_test_image_bytes()
    created = admin_client.post("/import/media", files={"file": ("a.jpg", content, "image/jpeg")}).json()

    resp = admin_client.patch(f"/medias/{created['id']}", json={"filename": "Photo de vacances"})
    assert resp.status_code == 200
    assert resp.json()["filename"] == "Photo de vacances"
    # le fichier physique n'est pas affecté par le renommage (juste le libellé affiché)
    assert resp.json()["chemin_stockage"] == created["chemin_stockage"]


def test_update_media_filename_empty_rejected(admin_client):
    content = _make_test_image_bytes()
    created = admin_client.post("/import/media", files={"file": ("a.jpg", content, "image/jpeg")}).json()

    resp = admin_client.patch(f"/medias/{created['id']}", json={"filename": "   "})
    assert resp.status_code == 400


def test_delete_media_removes_files_from_disk(admin_client):
    content = _make_test_image_bytes()
    created = admin_client.post("/import/media", files={"file": ("a.jpg", content, "image/jpeg")}).json()

    stored_path = os.path.join(settings.media_root, created["chemin_stockage"])
    vignette_path = os.path.join(settings.media_root, created["vignette_path"])
    assert os.path.exists(stored_path)
    assert os.path.exists(vignette_path)

    resp = admin_client.delete(f"/medias/{created['id']}")
    assert resp.status_code == 204
    assert not os.path.exists(stored_path)
    assert not os.path.exists(vignette_path)


def test_delete_media_not_found(admin_client):
    resp = admin_client.delete("/medias/999999")
    assert resp.status_code == 404
