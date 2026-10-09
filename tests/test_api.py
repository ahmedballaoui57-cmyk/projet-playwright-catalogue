import pytest


def _titres(reponse):
    return [livre["titre"] for livre in reponse.json()["elements"]]


def test_sante(client):
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_livres_sur_une_base_vide(client):
    assert client.get("/livres").json() == {"total": 0, "page": 1, "taille": 20, "elements": []}


def test_livres_renvoie_les_champs_d_un_livre(client, catalogue):
    reponse = client.get("/livres")
    assert reponse.status_code == 200
    assert reponse.json()["total"] == 4
    premier = reponse.json()["elements"][0]
    assert premier.pop("id") > 0
    assert premier == {"titre": "Atlas", "categorie": "Travel", "prix_gbp": 10.5, "note": 5,
                       "en_stock": True, "url": "https://site/atlas"}


def test_livres_pagination(client, catalogue):
    page = client.get("/livres", params={"taille": 3, "page": 2})
    # Le total reste celui de la recherche entière, pas celui de la page.
    assert page.json()["total"] == 4
    assert _titres(page) == ["Odes"]


@pytest.mark.parametrize("filtres, attendus", [
    ({"categorie": "travel"}, ["Atlas", "Boussole", "Carnet de voyage"]),
    ({"prix_min": 20, "prix_max": 30}, ["Boussole", "Odes"]),
    ({"note_min": 3}, ["Atlas", "Boussole"]),
    ({"en_stock": "false"}, ["Carnet de voyage"]),
    ({"q": "VOYAGE"}, ["Carnet de voyage"]),
    ({"q": "%"}, []),
    ({"categorie": "Travel", "en_stock": "true", "prix_max": 15}, ["Atlas"]),
    ({"categorie": "Inconnue"}, []),
])
def test_livres_filtres(client, catalogue, filtres, attendus):
    reponse = client.get("/livres", params=filtres)
    assert _titres(reponse) == attendus
    assert reponse.json()["total"] == len(attendus)


@pytest.mark.parametrize("tri, attendus", [
    ("-titre", ["Odes", "Carnet de voyage", "Boussole", "Atlas"]),
    ("prix_gbp", ["Atlas", "Boussole", "Odes", "Carnet de voyage"]),
    ("-note", ["Atlas", "Boussole", "Carnet de voyage", "Odes"]),
])
def test_livres_tri(client, catalogue, tri, attendus):
    assert _titres(client.get("/livres", params={"tri": tri})) == attendus


@pytest.mark.parametrize("parametres", [
    {"taille": 0}, {"taille": 101}, {"page": 0}, {"note_min": 6}, {"prix_min": -1}, {"tri": "url"},
])
def test_livres_refuse_les_parametres_invalides(client, parametres):
    assert client.get("/livres", params=parametres).status_code == 422


def test_livre_par_identifiant(client, catalogue):
    identifiant = client.get("/livres", params={"q": "Odes"}).json()["elements"][0]["id"]
    reponse = client.get(f"/livres/{identifiant}")
    assert reponse.status_code == 200
    assert reponse.json()["titre"] == "Odes"


def test_livre_inconnu(client):
    reponse = client.get("/livres/999")
    assert reponse.status_code == 404
    assert reponse.json() == {"detail": "Livre introuvable."}


def test_categories_avec_leur_nombre_de_livres(client, catalogue):
    categories = client.get("/categories").json()
    assert [(c["nom"], c["nb_livres"]) for c in categories] == [("Poetry", 1), ("Travel", 3)]


def test_indicateurs_par_categorie(client, catalogue):
    indicateurs = client.get("/categories/indicateurs").json()
    # La catégorie la plus fournie arrive en premier.
    assert indicateurs == [
        {"categorie": "Travel", "nb_livres": 3, "prix_moyen": 25.17, "prix_min": 10.5,
         "prix_max": 45.0, "note_moyenne": 3.33},
        {"categorie": "Poetry", "nb_livres": 1, "prix_moyen": 30.0, "prix_min": 30.0,
         "prix_max": 30.0, "note_moyenne": 1.0},
    ]
