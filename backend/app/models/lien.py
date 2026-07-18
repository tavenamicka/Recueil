from datetime import date as date_, datetime, time as time_

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lien(Base):
    __tablename__ = "liens"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    date: Mapped[date_ | None] = mapped_column(Date, index=True)
    heure: Mapped[time_ | None] = mapped_column(Time)
    domaine: Mapped[str | None] = mapped_column(String(255), index=True)
    # Texte non borné : certains og:title (posts Facebook notamment) dépassent
    # largement 1000 caractères.
    titre_brut: Mapped[str | None] = mapped_column(Text)
    titre_page: Mapped[str | None] = mapped_column(Text)
    categorie_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    date_ajout: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    favori: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    categorie: Mapped["Categorie"] = relationship(back_populates="liens")
