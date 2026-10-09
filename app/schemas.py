"""Schémas Pydantic : paramètres acceptés et réponses renvoyées par l'API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import StatutExtraction


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FiltresLivres(BaseModel):
    categorie: str | None = Field(None, description="nom exact de la catégorie, sans tenir compte de la casse")
    prix_min: float | None = Field(None, ge=0)
    prix_max: float | None = Field(None, ge=0)
    note_min: int | None = Field(None, ge=1, le=5)
    en_stock: bool | None = None
    q: str | None = Field(None, description="texte recherché dans le titre")
    tri: Literal["titre", "-titre", "prix_gbp", "-prix_gbp", "note", "-note"] = Field(
        "titre", description="préfixe - pour un tri décroissant")
    page: int = Field(1, ge=1)
    taille: int = Field(20, ge=1, le=100)


class LivreLu(Schema):
    id: int
    titre: str
    categorie: str
    prix_gbp: float
    note: int | None
    en_stock: bool
    url: str


class PageLivres(Schema):
    total: int
    page: int
    taille: int
    elements: list[LivreLu]


class CategorieLue(Schema):
    id: int
    nom: str
    nb_livres: int


class IndicateursCategorie(Schema):
    categorie: str
    nb_livres: int
    prix_moyen: float
    prix_min: float
    prix_max: float
    note_moyenne: float | None


class DemandeExtraction(BaseModel):
    max_categories: int | None = Field(
        None, ge=1, description="limite le nombre de catégories parcourues (pour un essai rapide)")


class ExtractionLue(Schema):
    id: int
    statut: StatutExtraction
    debut: datetime
    fin: datetime | None
    nb_livres: int | None
    erreur: str | None
