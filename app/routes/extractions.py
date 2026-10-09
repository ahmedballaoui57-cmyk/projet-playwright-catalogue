import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app import depot, service_extraction
from app.config import reglages
from app.db import obtenir_session
from app.models import Extraction
from app.schemas import DemandeExtraction, ExtractionLue
from extraction import ExtracteurCatalogue

journal = logging.getLogger(__name__)
routeur = APIRouter(prefix="/extractions", tags=["extractions"])
en_tete_cle = APIKeyHeader(name="X-API-Key", auto_error=False)


def verifier_cle(cle: Annotated[str | None, Depends(en_tete_cle)]) -> None:
    if cle is None or not secrets.compare_digest(cle.encode(), reglages.cle_api.encode()):
        raise HTTPException(401, "Clé d'API absente ou invalide.")


def _executer_en_fond(extraction_id: int, extracteur: ExtracteurCatalogue) -> None:
    try:
        service_extraction.executer(extraction_id, extracteur)
    except Exception:
        # L'échec est déjà consigné en base ; on le trace aussi dans les journaux du serveur.
        journal.exception("Extraction %s échouée", extraction_id)


@routeur.post("", response_model=ExtractionLue, status_code=202,
              dependencies=[Depends(verifier_cle)])
def lancer_extraction(taches: BackgroundTasks,
                      session: Annotated[Session, Depends(obtenir_session)],
                      demande: Annotated[DemandeExtraction, Body()] = DemandeExtraction()):
    """Lance l'extraction en tâche de fond ; son avancement se lit sur GET /extractions/{id}."""
    try:
        extraction = service_extraction.demarrer(session)
    except service_extraction.ExtractionDejaEnCours:
        raise HTTPException(409, "Une extraction est déjà en cours.") from None

    extracteur = ExtracteurCatalogue(reglages.navigateur, max_categories=demande.max_categories)
    taches.add_task(_executer_en_fond, extraction.id, extracteur)
    return extraction


@routeur.get("", response_model=list[ExtractionLue])
def lister_extractions(session: Annotated[Session, Depends(obtenir_session)]):
    """Les 20 dernières extractions, la plus récente en premier."""
    return depot.lister_extractions(session)


@routeur.get("/{extraction_id}", response_model=ExtractionLue)
def lire_extraction(extraction_id: int, session: Annotated[Session, Depends(obtenir_session)]):
    extraction = session.get(Extraction, extraction_id)
    if extraction is None:
        raise HTTPException(404, "Extraction introuvable.")
    return extraction
