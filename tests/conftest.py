import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import make_url, text

import extraction
from app import depot
from app.config import reglages
from app.db import SessionLocale, moteur
from app.main import app
from traitement import nettoyer

SITE = Path(__file__).parent / "site"


class ServeurSilencieux(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def navigateur():
    """Par défaut le Chrome du poste ; NAVIGATEUR_TESTS=chromium utilise celui installé par Playwright."""
    return os.environ.get("NAVIGATEUR_TESTS", "chrome")


@pytest.fixture(scope="session")
def site():
    """Sert tests/site en local et y redirige l'extracteur : aucun accès au réseau."""
    serveur = ThreadingHTTPServer(("127.0.0.1", 0), partial(ServeurSilencieux, directory=str(SITE)))
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{serveur.server_port}/"

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(extraction, "URL_ACCUEIL", url)
        yield url

    serveur.shutdown()
    serveur.server_close()


@pytest.fixture(scope="session")
def base():
    """Crée les tables par les migrations Alembic, sur une base PostgreSQL réservée aux tests."""
    if "DATABASE_URL" not in os.environ:
        pytest.skip("PostgreSQL requis : docker compose --profile tests run --rm tests")
    # Les tests vident les tables : on refuse toute base qui n'est pas explicitement de test.
    if not make_url(reglages.database_url).database.endswith("_test"):
        pytest.fail("DATABASE_URL doit désigner une base dont le nom finit par _test.")
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def session(base):
    with moteur.begin() as connexion:
        connexion.execute(text("TRUNCATE categories, extractions, livres RESTART IDENTITY CASCADE"))
    with SessionLocale() as session:
        yield session


@pytest.fixture
def client(session):
    return TestClient(app)


@pytest.fixture
def catalogue(session):
    """Quatre livres dans deux catégories, passés par le même nettoyage que l'extraction."""
    livres = [
        {"titre": "Atlas", "prix": "£10.50", "note": "Five", "disponibilite": "In stock",
         "url": "https://site/atlas", "categorie": "Travel"},
        {"titre": "Boussole", "prix": "£20.00", "note": "Three", "disponibilite": "In stock",
         "url": "https://site/boussole", "categorie": "Travel"},
        {"titre": "Carnet de voyage", "prix": "£45.00", "note": "Two", "disponibilite": "Out of stock",
         "url": "https://site/carnet", "categorie": "Travel"},
        {"titre": "Odes", "prix": "£30.00", "note": "One", "disponibilite": "In stock",
         "url": "https://site/odes", "categorie": "Poetry"},
    ]
    depot.enregistrer_livres(session, nettoyer(livres))
    session.commit()
