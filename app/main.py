"""API FastAPI du catalogue : lecture des livres et lancement des extractions."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import SessionLocale
from app.routes import categories, extractions, livres, sante
from app.service_extraction import cloturer_extractions_interrompues


@asynccontextmanager
async def cycle_de_vie(app: FastAPI):
    with SessionLocale() as session:
        cloturer_extractions_interrompues(session)
    yield


app = FastAPI(title="Catalogue de livres", version="1.0.0", description=__doc__,
              lifespan=cycle_de_vie)
app.include_router(sante.routeur)
app.include_router(livres.routeur)
app.include_router(categories.routeur)
app.include_router(extractions.routeur)
