"""Tests unitaires pour les fonctions de media_service.py qui ne passent pas par un
endpoint HTTP (contrairement à test_medias.py, qui teste /import/media)."""

import io
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from app.core.config import settings
from app.services.media_service import download_lien_thumbnail


def _make_test_image_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


@patch("app.services.media_service.requests.get")
def test_download_lien_thumbnail_stocke_localement(mock_get, _fresh_media_dir):
    mock_get.return_value = Mock(content=_make_test_image_bytes())
    mock_get.return_value.raise_for_status = Mock()

    vignette_path = download_lien_thumbnail("https://example.com/photo.jpg")

    assert vignette_path is not None
    assert vignette_path.startswith("vignettes/")
    assert (Path(settings.media_root) / vignette_path).exists()


@patch("app.services.media_service.requests.get")
def test_download_lien_thumbnail_none_si_echec_reseau(mock_get, _fresh_media_dir):
    mock_get.side_effect = Exception("timeout")
    assert download_lien_thumbnail("https://example.com/photo.jpg") is None


@patch("app.services.media_service.requests.get")
def test_download_lien_thumbnail_none_si_pas_une_image(mock_get, _fresh_media_dir):
    mock_get.return_value = Mock(content=b"ceci n'est pas une image")
    mock_get.return_value.raise_for_status = Mock()
    assert download_lien_thumbnail("https://example.com/pas-une-image") is None
