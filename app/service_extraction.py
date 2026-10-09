"""Déroulement d'une extraction : navigateur -> nettoyage -> base, avec suivi du statut."""

from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import depot
from app.db import SessionLocale
from app.models import Extraction, StatutExtraction
from extraction import ExtracteurCatalogue
from traitement import nettoyer

AUCUN_LIVRE = "Aucun livre extrait : la structure du site a peut-être changé."


class ExtractionDejaEnCours(Exception):
    pass


def demarrer(session: Session) -> Extraction:
    """Ouvre une extraction ; l'index unique de la base garantit qu'il n'y en a qu'une en cours."""
    extraction = Extraction()
    session.add(extraction)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ExtractionDejaEnCours from None
    return extraction


def executer(extraction_id: int, extracteur: ExtracteurCatalogue) -> pd.DataFrame:
    """Extrait, nettoie et enregistre les livres ; l'issue est consignée dans l'extraction."""
    with SessionLocale() as session:
        extraction = session.get(Extraction, extraction_id)
        try:
            livres = extracteur.extraire()
            if not livres:
                raise ValueError(AUCUN_LIVRE)
            df = nettoyer(livres)
            extraction.nb_livres = depot.enregistrer_livres(session, df, extraction_id)
            extraction.statut = StatutExtraction.TERMINEE.value
            return df
        except Exception as erreur:
            # Aucun livre de l'extraction échouée n'est conservé.
            session.rollback()
            extraction.statut = StatutExtraction.ECHOUEE.value
            extraction.erreur = str(erreur)
            raise
        finally:
            extraction.fin = datetime.now(timezone.utc)
            session.commit()


def cloturer_extractions_interrompues(session: Session) -> None:
    """Au démarrage de l'API : une extraction encore « en cours » a été coupée par l'arrêt."""
    session.execute(
        update(Extraction)
        .where(Extraction.statut == StatutExtraction.EN_COURS.value)
        .values(statut=StatutExtraction.ECHOUEE.value, fin=datetime.now(timezone.utc),
                erreur="Interrompue par l'arrêt de l'API."))
    session.commit()
