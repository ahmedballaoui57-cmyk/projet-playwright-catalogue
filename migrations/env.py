"""Environnement Alembic : applique les migrations sur la base décrite par DATABASE_URL."""

from alembic import context

from app import models  # noqa: F401  (enregistre les tables dans Base.metadata)
from app.db import Base, moteur

with moteur.connect() as connexion:
    context.configure(connection=connexion, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
