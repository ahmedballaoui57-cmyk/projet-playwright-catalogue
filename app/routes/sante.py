from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import obtenir_session

routeur = APIRouter(tags=["santé"])


@routeur.get("/sante")
def sante(session: Annotated[Session, Depends(obtenir_session)]):
    """Vérifie que l'API répond et qu'elle joint la base."""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(503, "Base de données injoignable.") from None
    return {"statut": "ok"}
