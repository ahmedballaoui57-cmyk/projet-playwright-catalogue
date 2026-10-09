from decimal import Decimal

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select

from app import depot
from app.models import Categorie, Livre
from traitement import nettoyer


def _livre(**champs):
    return {"titre": "Atlas", "prix": "£10.50", "note": "Five", "disponibilite": "In stock",
            "url": "https://site/atlas", "categorie": "Travel", **champs}


def test_les_migrations_correspondent_aux_modeles(base):
    # Échoue si un modèle a changé sans qu'une migration ait été écrite.
    command.check(Config("alembic.ini"))


def test_enregistrer_livres_cree_livres_et_categories(session):
    nb = depot.enregistrer_livres(session, nettoyer([
        _livre(), _livre(titre="Odes", url="https://site/odes", categorie="Poetry")]))
    session.commit()

    assert nb == 2
    assert session.scalars(select(Categorie.nom).order_by(Categorie.nom)).all() == ["Poetry", "Travel"]
    atlas = session.scalars(select(Livre).where(Livre.url == "https://site/atlas")).one()
    assert (atlas.titre, atlas.prix_gbp, atlas.note, atlas.en_stock) == ("Atlas", Decimal("10.50"), 5, True)
    assert atlas.categorie.nom == "Travel"


def test_une_nouvelle_extraction_met_a_jour_sans_dupliquer(session):
    depot.enregistrer_livres(session, nettoyer([_livre()]))
    session.commit()

    depot.enregistrer_livres(session, nettoyer([
        _livre(prix="£12.00", disponibilite="Out of stock", categorie="Poetry")]))
    session.commit()

    assert session.scalar(select(func.count()).select_from(Livre)) == 1
    atlas = session.scalars(select(Livre)).one()
    session.refresh(atlas)
    assert (atlas.prix_gbp, atlas.en_stock, atlas.categorie.nom) == (Decimal("12.00"), False, "Poetry")


def test_une_note_inconnue_est_enregistree_vide(session):
    depot.enregistrer_livres(session, nettoyer([_livre(note="Zero")]))
    session.commit()

    assert session.scalars(select(Livre.note)).one() is None
