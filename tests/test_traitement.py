import pytest

from traitement import COLONNES, indicateurs_par_categorie, nettoyer


@pytest.fixture
def livres():
    """Lignes brutes telles que renvoyées par l'extraction, avec un doublon."""
    return [
        {"titre": "B", "prix": "£20.00", "note": "Three", "disponibilite": "In stock",
         "url": "https://site/b", "categorie": "Travel"},
        {"titre": "A", "prix": "£10.50", "note": "Five", "disponibilite": "In stock",
         "url": "https://site/a", "categorie": "Travel"},
        {"titre": "C", "prix": "Â£30.00", "note": "One", "disponibilite": "Out of stock",
         "url": "https://site/c", "categorie": "Poetry"},
        {"titre": "A", "prix": "£10.50", "note": "Five", "disponibilite": "In stock",
         "url": "https://site/a", "categorie": "Travel"},
    ]


def test_nettoyer_convertit_les_prix_en_nombres(livres):
    df = nettoyer(livres)
    assert df.set_index("titre")["prix_gbp"].to_dict() == {"A": 10.5, "B": 20.0, "C": 30.0}


def test_nettoyer_convertit_les_notes_en_chiffres(livres):
    df = nettoyer(livres)
    assert df.set_index("titre")["note"].to_dict() == {"A": 5, "B": 3, "C": 1}


def test_nettoyer_detecte_le_stock(livres):
    df = nettoyer(livres)
    assert df.set_index("titre")["en_stock"].to_dict() == {"A": True, "B": True, "C": False}


def test_nettoyer_supprime_les_doublons(livres):
    df = nettoyer(livres)
    assert len(df) == 3


def test_nettoyer_renvoie_les_colonnes_attendues(livres):
    df = nettoyer(livres)
    assert list(df.columns) == COLONNES


def test_indicateurs_par_categorie(livres):
    kpi = indicateurs_par_categorie(nettoyer(livres))

    # La catégorie la plus fournie arrive en premier.
    travel = kpi.iloc[0]
    assert travel["categorie"] == "Travel"
    assert travel["nb_livres"] == 2
    assert travel["prix_moyen"] == pytest.approx(15.25)
    assert travel["prix_min"] == pytest.approx(10.5)
    assert travel["prix_max"] == pytest.approx(20.0)
    assert travel["note_moyenne"] == pytest.approx(4.0)
    assert len(kpi) == 2
