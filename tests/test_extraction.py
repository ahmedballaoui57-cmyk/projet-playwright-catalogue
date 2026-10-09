import pytest

from extraction import ExtracteurCatalogue


@pytest.fixture(scope="module")
def livres(site, navigateur):
    return ExtracteurCatalogue(navigateur).extraire()


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


def test_max_categories_limite_le_parcours(site, navigateur):
    livres = ExtracteurCatalogue(navigateur, max_categories=1).extraire()
    assert {livre["categorie"] for livre in livres} == {"Travel"}
    assert len(livres) == 3
