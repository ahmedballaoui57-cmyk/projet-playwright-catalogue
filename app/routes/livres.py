from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import depot
from app.db import obtenir_session
from app.schemas import FiltresLivres, LivreLu, PageLivres

routeur = APIRouter(prefix="/livres", tags=["livres"])


@routeur.get("", response_model=PageLivres)
def lister_livres(filtres: Annotated[FiltresLivres, Query()],
                  session: Annotated[Session, Depends(obtenir_session)]):
    total, lignes = depot.lister_livres(session, filtres)
    return {"total": total, "page": filtres.page, "taille": filtres.taille, "elements": lignes}


@routeur.get("/{livre_id}", response_model=LivreLu)
def lire_livre(livre_id: int, session: Annotated[Session, Depends(obtenir_session)]):
    livre = depot.lire_livre(session, livre_id)
    if livre is None:
        raise HTTPException(404, "Livre introuvable.")
    return livre
