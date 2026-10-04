import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import extraction
from extraction import ExtracteurCatalogue

SITE = Path(__file__).parent / "site"

# Par défaut le Chrome du poste ; NAVIGATEUR_TESTS=chromium utilise celui installé par Playwright.
NAVIGATEUR = os.environ.get("NAVIGATEUR_TESTS", "chrome")


class ServeurSilencieux(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
def livres(site):
    return ExtracteurCatalogue(NAVIGATEUR).extraire()


def test_extraire_parcourt_toutes_les_categories(livres):
    # Le lien "Books" du menu, qui englobe tout le catalogue, n'est pas une catégorie.
    assert [livre["categorie"] for livre in livres] == ["Travel", "Travel", "Travel", "Poetry"]


def test_extraire_suit_la_pagination(livres):
    titres = [livre["titre"] for livre in livres if livre["categorie"] == "Travel"]
    assert titres == ["Un titre long qui est coupé à l'affichage", "Livre B", "Livre C"]


def test_extraire_lit_les_champs_d_un_livre(livres, site):
    assert livres[0] == {
        "titre": "Un titre long qui est coupé à l'affichage",
        "prix": "£45.17",
        "note": "Three",
        "disponibilite": "In stock",
        "url": site + "travel/livre-a.html",
        "categorie": "Travel",
    }


def test_max_categories_limite_le_parcours(site):
    livres = ExtracteurCatalogue(NAVIGATEUR, max_categories=1).extraire()
    assert {livre["categorie"] for livre in livres} == {"Travel"}
    assert len(livres) == 3
