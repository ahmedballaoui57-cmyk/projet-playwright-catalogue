import pytest

from app.config import reglages
from app.models import Extraction
from app.service_extraction import cloturer_extractions_interrompues, demarrer
from extraction import ExtracteurCatalogue

CLE = {"X-API-Key": reglages.cle_api}


@pytest.fixture
def navigateur_api(site, navigateur, monkeypatch):
    """L'API extrait le mini-site local avec le navigateur des tests."""
    monkeypatch.setattr(reglages, "navigateur", navigateur)


@pytest.mark.parametrize("en_tetes", [{}, {"X-API-Key": "mauvaise-cle"}])
def test_lancer_une_extraction_exige_la_cle(client, en_tetes):
    reponse = client.post("/extractions", headers=en_tetes)
    assert reponse.status_code == 401
    assert client.get("/extractions").json() == []


def test_extraction_complete_par_l_api(client, navigateur_api):
    reponse = client.post("/extractions", headers=CLE)
    assert reponse.status_code == 202
    assert reponse.json()["statut"] == "en_cours"

    # Le client de test attend la fin de la tâche de fond avant de rendre la main.
    extraction = client.get(f"/extractions/{reponse.json()['id']}").json()
    assert extraction["statut"] == "terminee"
    assert extraction["nb_livres"] == 4
    assert extraction["fin"] is not None
    assert extraction["erreur"] is None

    livres = client.get("/livres", params={"categorie": "Travel", "tri": "prix_gbp"}).json()
    assert livres["total"] == 3
    assert livres["elements"][-1]["titre"] == "Un titre long qui est coupé à l'affichage"
    assert livres["elements"][-1]["prix_gbp"] == 45.17


def test_relancer_une_extraction_ne_duplique_pas_les_livres(client, navigateur_api):
    client.post("/extractions", headers=CLE)
    client.post("/extractions", headers=CLE)

    assert client.get("/livres").json()["total"] == 4
    assert [e["statut"] for e in client.get("/extractions").json()] == ["terminee", "terminee"]


def test_max_categories_est_transmis_a_l_extracteur(client, navigateur_api):
    client.post("/extractions", headers=CLE, json={"max_categories": 1})
    assert [c["nom"] for c in client.get("/categories").json()] == ["Travel"]


def test_une_seule_extraction_a_la_fois(client, session):
    demarrer(session)

    reponse = client.post("/extractions", headers=CLE)
    assert reponse.status_code == 409
    assert len(client.get("/extractions").json()) == 1


def test_une_extraction_echouee_est_consignee(client, monkeypatch):
    def extraire_en_panne(self):
        raise RuntimeError("site injoignable")
    monkeypatch.setattr(ExtracteurCatalogue, "extraire", extraire_en_panne)

    identifiant = client.post("/extractions", headers=CLE).json()["id"]

    extraction = client.get(f"/extractions/{identifiant}").json()
    assert extraction["statut"] == "echouee"
    assert extraction["erreur"] == "site injoignable"
    assert extraction["fin"] is not None
    # L'échec libère le verrou : une nouvelle extraction peut être lancée.
    assert client.post("/extractions", headers=CLE).status_code == 202


def test_une_extraction_sans_livre_est_un_echec(client, monkeypatch):
    monkeypatch.setattr(ExtracteurCatalogue, "extraire", lambda self: [])

    identifiant = client.post("/extractions", headers=CLE).json()["id"]

    extraction = client.get(f"/extractions/{identifiant}").json()
    assert extraction["statut"] == "echouee"
    assert "Aucun livre extrait" in extraction["erreur"]


def test_extraction_inconnue(client):
    assert client.get("/extractions/999").status_code == 404


def test_les_extractions_interrompues_sont_cloturees_au_demarrage(session):
    extraction = demarrer(session)

    cloturer_extractions_interrompues(session)

    session.refresh(extraction)
    assert extraction.statut == "echouee"
    assert extraction.fin is not None
    assert session.get(Extraction, extraction.id).erreur == "Interrompue par l'arrêt de l'API."
