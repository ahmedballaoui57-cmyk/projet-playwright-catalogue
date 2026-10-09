"""Tables PostgreSQL : catégories, livres et historique des extractions."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, SmallInteger, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class StatutExtraction(StrEnum):
    EN_COURS = "en_cours"
    TERMINEE = "terminee"
    ECHOUEE = "echouee"


class Categorie(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True)


class Extraction(Base):
    __tablename__ = "extractions"
    # Index unique partiel : la base elle-même refuse deux extractions en cours.
    __table_args__ = (
        Index("uq_extractions_en_cours", "statut", unique=True,
              postgresql_where=text("statut = 'en_cours'")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    statut: Mapped[str] = mapped_column(String(20), default=StatutExtraction.EN_COURS.value)
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    nb_livres: Mapped[int | None]
    erreur: Mapped[str | None] = mapped_column(Text)


class Livre(Base):
    __tablename__ = "livres"

    id: Mapped[int] = mapped_column(primary_key=True)
    categorie_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    titre: Mapped[str] = mapped_column(Text)
    prix_gbp: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    note: Mapped[int | None] = mapped_column(SmallInteger)
    en_stock: Mapped[bool]
    # L'URL identifie le livre : c'est la clé de la mise à jour lors d'une nouvelle extraction.
    url: Mapped[str] = mapped_column(Text, unique=True)
    extraction_id: Mapped[int | None] = mapped_column(
        ForeignKey("extractions.id", ondelete="SET NULL"))
    maj_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    categorie: Mapped[Categorie] = relationship()
