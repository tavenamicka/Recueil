import re
import subprocess
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.media import Media, MediaType

EXTENSION_MAP: dict[str, MediaType] = {
    ".jpg": MediaType.image,
    ".jpeg": MediaType.image,
    ".png": MediaType.image,
    ".webp": MediaType.image,
    ".mp4": MediaType.video,
    ".mov": MediaType.video,
    ".mp3": MediaType.audio,
    ".wav": MediaType.audio,
}

THUMBNAIL_SIZE = (320, 320)

# ex: IMG-20260301-WA0000.jpg -> 2026-03-01
WHATSAPP_FILENAME_RE = re.compile(r"-(\d{4})(\d{2})(\d{2})-WA")


def _detect_type(filename: str) -> MediaType:
    ext = Path(filename).suffix.lower()
    media_type = EXTENSION_MAP.get(ext)
    if media_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"Format {ext or 'inconnu'} non supporté pour l'instant. "
            "Formats acceptés : .jpg .png .webp .mp4 .mov .mp3 .wav.",
        )
    return media_type


def _extract_date_from_filename(filename: str) -> datetime | None:
    m = WHATSAPP_FILENAME_RE.search(filename)
    if not m:
        return None
    year, month, day = (int(g) for g in m.groups())
    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def _make_thumbnail_image(source: Path, dest: Path) -> None:
    with Image.open(source) as img:
        img.thumbnail(THUMBNAIL_SIZE)
        img.convert("RGB").save(dest, "JPEG")


def _make_thumbnail_video(source: Path, dest: Path) -> bool:
    result = subprocess.run(
        ["ffmpeg", "-y", "-ss", "00:00:01", "-i", str(source), "-frames:v", "1", str(dest)],
        capture_output=True,
    )
    return result.returncode == 0 and dest.exists()


def _extract_duration_seconds(source: Path) -> int | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(source),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        return round(float(result.stdout.strip()))
    except (ValueError, OSError):
        return None


def save_media(db: Session, file: UploadFile) -> Media:
    media_type = _detect_type(file.filename)

    media_dir = Path(settings.media_root) / media_type.value
    media_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid4().hex}{Path(file.filename).suffix.lower()}"
    stored_path = media_dir / stored_name
    with stored_path.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            out.write(chunk)
    taille_octets = stored_path.stat().st_size

    vignette_path: str | None = None
    if media_type in (MediaType.image, MediaType.video):
        thumb_dir = Path(settings.media_root) / "vignettes"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = thumb_dir / f"{stored_path.stem}.jpg"
        try:
            if media_type == MediaType.image:
                _make_thumbnail_image(stored_path, thumb_path)
                vignette_path = f"vignettes/{thumb_path.name}"
            elif _make_thumbnail_video(stored_path, thumb_path):
                vignette_path = f"vignettes/{thumb_path.name}"
        except Exception:
            vignette_path = None

    duree_secondes: int | None = None
    if media_type in (MediaType.video, MediaType.audio):
        duree_secondes = _extract_duration_seconds(stored_path)

    media = Media(
        filename=file.filename,
        type=media_type,
        # chemins relatifs à MEDIA_ROOT, servis tels quels via le mount StaticFiles /media
        chemin_stockage=f"{media_type.value}/{stored_name}",
        vignette_path=vignette_path,
        date_originale=_extract_date_from_filename(file.filename),
        taille_octets=taille_octets,
        duree_secondes=duree_secondes,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media
