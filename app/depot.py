"""Lectures et écritures en base : tout le SQL de l'application est ici."""

from collections.abc import Sequence

import pandas as pd
from sqlalchemy import Row, desc, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Categorie, Extraction, Livre
from app.schemas import FiltresLivres

SELECTION_LIVRES = select(
    Livre.id, Livre.titre, Categorie.nom.label("categorie"),
    Livre.prix_gbp, Livre.note, Livre.en_stock, Livre.url,
).join(Livre.categorie)

CHAMPS_MIS_A_JOUR = ["categorie_id", "titre", "prix_gbp", "note", "en_stock", "extraction_id"]


def enregistrer_livres(session: Session, df: pd.DataFrame, extraction_id: int | None = None) -> int:
    """Insère les livres nettoyés ; un livre déjà connu (même URL) est mis à jour."""
    noms = df["categorie"].unique().tolist()
    session.execute(
        insert(Categorie).values([{"nom": nom} for nom in noms]).on_conflict_do_nothing())
    ids = dict(session.execute(
        select(Categorie.nom, Categorie.id).where(Categorie.nom.in_(noms))).all())

    # Types Python natifs, et None à la place de NaN (note inconnue).
    lignes = df.astype(object).where(df.notna(), None).to_dict("records")
    for ligne in lignes:
        ligne["categorie_id"] = ids[ligne.pop("categorie")]
        ligne["extraction_id"] = extraction_id

    requete = insert(Livre).values(lignes)
    mises_a_jour = {champ: requete.excluded[champ] for champ in CHAMPS_MIS_A_JOUR}
    session.execute(requete.on_conflict_do_update(
        index_elements=["url"], set_={**mises_a_jour, "maj_le": func.now()}))
    return len(lignes)


def lister_livres(session: Session, filtres: FiltresLivres) -> tuple[int, Sequence[Row]]:
    conditions = []
    if filtres.categorie:
        conditions.append(func.lower(Categorie.nom) == filtres.categorie.lower())
    if filtres.prix_min is not None:
        conditions.append(Livre.prix_gbp >= filtres.prix_min)
    if filtres.prix_max is not None:
        conditions.append(Livre.prix_gbp <= filtres.prix_max)
    if filtres.note_min is not None:
        conditions.append(Livre.note >= filtres.note_min)
    if filtres.en_stock is not None:
        conditions.append(Livre.en_stock == filtres.en_stock)
    if filtres.q:
        conditions.append(Livre.titre.icontains(filtres.q, autoescape=True))

    requete = SELECTION_LIVRES.where(*conditions)
    total = session.scalar(select(func.count()).select_from(requete.subquery()))

    colonne = getattr(Livre, filtres.tri.lstrip("-"))
    ordre = colonne.desc() if filtres.tri.startswith("-") else colonne.asc()
    # Livre.id départage les ex æquo : la pagination reste stable d'une page à l'autre.
    lignes = session.execute(
        requete.order_by(ordre, Livre.id)
        .limit(filtres.taille).offset((filtres.page - 1) * filtres.taille)).all()
    return total, lignes


def lire_livre(session: Session, livre_id: int) -> Row | None:
    return session.execute(SELECTION_LIVRES.where(Livre.id == livre_id)).one_or_none()


def lister_categories(session: Session) -> Sequence[Row]:
    return session.execute(
        select(Categorie.id, Categorie.nom, func.count(Livre.id).label("nb_livres"))
        .outerjoin(Livre).group_by(Categorie.id).order_by(Categorie.nom)).all()


def indicateurs_par_categorie(session: Session) -> Sequence[Row]:
    """Mêmes indicateurs que le rapport Excel, calculés par PostgreSQL."""
    return session.execute(
        select(
            Categorie.nom.label("categorie"),
            func.count(Livre.id).label("nb_livres"),
            func.round(func.avg(Livre.prix_gbp), 2).label("prix_moyen"),
            func.min(Livre.prix_gbp).label("prix_min"),
            func.max(Livre.prix_gbp).label("prix_max"),
            func.round(func.avg(Livre.note), 2).label("note_moyenne"),
        )
        .select_from(Livre).join(Livre.categorie)
        .group_by(Categorie.nom).order_by(desc("nb_livres"), Categorie.nom)).all()


def lister_extractions(session: Session, limite: int = 20) -> Sequence[Extraction]:
    return session.scalars(
        select(Extraction).order_by(Extraction.id.desc()).limit(limite)).all()
