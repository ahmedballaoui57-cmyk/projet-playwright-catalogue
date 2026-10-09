from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import depot
from app.db import obtenir_session
from app.schemas import CategorieLue, IndicateursCategorie

routeur = APIRouter(prefix="/categories", tags=["catégories"])


@routeur.get("", response_model=list[CategorieLue])
def lister_categories(session: Annotated[Session, Depends(obtenir_session)]):
    return depot.lister_categories(session)


@routeur.get("/indicateurs", response_model=list[IndicateursCategorie])
def indicateurs(session: Annotated[Session, Depends(obtenir_session)]):
    return depot.indicateurs_par_categorie(session)
