"""Connexion à PostgreSQL avec SQLAlchemy."""

from collections.abc import Iterator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import reglages

# Noms de contraintes explicites : les migrations Alembic peuvent les modifier sans deviner.
CONVENTION = {
    "pk": "pk_%(table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ix": "ix_%(column_0_label)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}

moteur = create_engine(reglages.database_url, pool_pre_ping=True)
SessionLocale = sessionmaker(moteur, expire_on_commit=False)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENTION)


def obtenir_session() -> Iterator[Session]:
    """Dépendance FastAPI : une session par requête."""
    with SessionLocale() as session:
        yield session
