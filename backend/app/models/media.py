import enum
from datetime import datetime

from sqlalchemy import Boolean, BigInteger, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MediaType(str, enum.Enum):
    image = "image"
    video = "video"
    audio = "audio"


class Media(Base):
    __tablename__ = "medias"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[MediaType] = mapped_column(Enum(MediaType, name="media_type"), nullable=False)
    chemin_stockage: Mapped[str] = mapped_column(String(1000), nullable=False)
    vignette_path: Mapped[str | None] = mapped_column(String(1000))
    date_originale: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_upload: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    taille_octets: Mapped[int] = mapped_column(BigInteger, nullable=False)
    favori: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    duree_secondes: Mapped[int | None] = mapped_column(Integer)
