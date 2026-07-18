from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Categorie(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    couleur: Mapped[str] = mapped_column(String(7), nullable=False)

    liens: Mapped[list["Lien"]] = relationship(back_populates="categorie")
