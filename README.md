# Catalogue de livres : extraction Playwright, PostgreSQL, API FastAPI, Docker

Projet backend Python qui extrait un catalogue web, le stocke dans PostgreSQL et l'expose par une API REST :

1. **Extraction** (Playwright) : ouvre un navigateur, parcourt les 50 catégories de [books.toscrape.com](https://books.toscrape.com/) en suivant la pagination, et collecte environ 1 000 livres (titre, prix, note, disponibilité).
2. **Traitement** (Pandas) : nettoie les textes bruts (prix, notes) et supprime les doublons.
3. **Stockage** (PostgreSQL, SQLAlchemy, Alembic) : enregistre les livres ; relancer une extraction met à jour les livres existants au lieu de les dupliquer.
4. **API** (FastAPI) : recherche paginée et filtrée, indicateurs par catégorie, lancement et suivi des extractions.
5. **Rapport** (OpenPyXL) : génère en plus un rapport Excel mis en forme et un fichier CSV.

Le site cible est un site d'entraînement public, conçu pour être extrait.

```
Playwright ──> Pandas ──> PostgreSQL ──> API FastAPI
                              └────────> rapport Excel / CSV
```

## Démarrage avec Docker

Seul Docker est nécessaire.

```bash
docker compose up --build
```

Cette commande démarre PostgreSQL, applique les migrations puis lance l'API sur http://localhost:8000. La documentation interactive est sur http://localhost:8000/docs.

La base est vide au premier démarrage. Pour la remplir, lancer une extraction par l'API :

```bash
curl -X POST http://localhost:8000/extractions -H "X-API-Key: changez-moi"
```

ou par la ligne de commande, qui génère aussi le rapport Excel dans `sortie/` :

```bash
docker compose run --rm api python main.py
```

Le mot de passe de la base et la clé d'API se changent dans un fichier `.env` (modèle : `.env.example`).

## API

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/sante` | vérifie que l'API répond et joint la base |
| GET | `/livres` | liste paginée, filtrée et triée |
| GET | `/livres/{id}` | un livre |
| GET | `/categories` | catégories avec leur nombre de livres |
| GET | `/categories/indicateurs` | nombre de livres, prix moyen, minimum, maximum et note moyenne par catégorie |
| POST | `/extractions` | lance une extraction en tâche de fond (clé d'API exigée) |
| GET | `/extractions` | les 20 dernières extractions |
| GET | `/extractions/{id}` | état d'une extraction : `en_cours`, `terminee` ou `echouee` |

Paramètres de `GET /livres` :

| Paramètre | Effet |
|---|---|
| `categorie` | nom exact de la catégorie, sans tenir compte de la casse |
| `prix_min`, `prix_max` | bornes de prix en livres sterling |
| `note_min` | note minimale, de 1 à 5 |
| `en_stock` | `true` ou `false` |
| `q` | texte recherché dans le titre |
| `tri` | `titre`, `prix_gbp` ou `note` ; préfixe `-` pour un tri décroissant |
| `page`, `taille` | pagination (20 livres par page par défaut, 100 au plus) |

Exemple : `GET /livres?categorie=Travel&prix_max=30&tri=-note`

`POST /extractions` répond `202` tout de suite et l'extraction continue en arrière-plan. Il répond `401` sans la clé d'API (en-tête `X-API-Key`) et `409` si une extraction est déjà en cours. Le corps `{"max_categories": 3}` limite le parcours, pour un essai rapide.

## Tests et intégration continue

```bash
docker compose --profile tests run --rm tests
```

Cette commande construit l'image de test, démarre un PostgreSQL jetable (en mémoire, distinct de la base de l'application) et lance pytest. Les tests n'accèdent pas au réseau :

- les tests de la base et de l'API tournent sur un vrai PostgreSQL, dont les tables sont créées par les migrations Alembic ;
- les tests d'extraction lancent un vrai navigateur sur une copie miniature du site (`tests/site/`), servie en local ;
- un test vérifie que les migrations correspondent aux modèles.

À chaque envoi de code sur GitHub, le workflow `.github/workflows/tests.yml` (GitHub Actions) lance la même commande.

## Tests Postman

La collection `tests/postman/catalogue.postman_collection.json` teste l'API en fonctionnement (27 requêtes, 80 vérifications) : codes de réponse, structure des données, filtres, tris, erreurs et cycle complet d'une extraction.

Dans Postman : **Import**, choisir le fichier, puis renseigner la variable de collection `cle_api` avec la valeur de `CLE_API` du fichier `.env`. Lancer ensuite toute la collection (**Run**) : le dossier Extractions remplit la base avant les tests de lecture.

En ligne de commande, avec Newman dans Docker (l'application doit être démarrée) :

```bash
docker run --rm --network projet-playwright-catalogue_default -v "./tests/postman:/etc/newman" postman/newman:alpine run catalogue.postman_collection.json --env-var "baseUrl=http://api:8000" --env-var "cle_api=VOTRE_CLE"
```

## Utilisation sans Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

Le script pilote alors le Chrome déjà installé sur le poste. Sans PostgreSQL, il génère seulement les fichiers :

```bash
python main.py --sans-base
```

| Option | Effet |
|---|---|
| `--max-categories 3` | essai rapide sur 3 catégories |
| `--visible` | affiche le navigateur pendant l'extraction |
| `--navigateur msedge` | utilise Edge à la place de Chrome |
| `--navigateur chromium` | utilise le Chromium de Playwright (après `playwright install chromium`) |
| `--sortie dossier` | dossier des fichiers générés (par défaut `sortie`) |
| `--sans-base` | n'écrit pas dans PostgreSQL |

Avec un PostgreSQL accessible, renseigner son adresse dans la variable `DATABASE_URL` (par exemple `postgresql+psycopg://catalogue:catalogue@localhost:5432/catalogue`), puis :

```bash
alembic upgrade head
python main.py
uvicorn app.main:app --reload
```

`pytest` lance les tests ; ceux qui demandent PostgreSQL sont ignorés si `DATABASE_URL` n'est pas définie. Comme ils vident les tables, ils refusent toute base dont le nom ne finit pas par `_test`.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `extraction.py` | classe `ExtracteurCatalogue` : navigation, pagination, lecture des pages |
| `traitement.py` | nettoyage et indicateurs avec Pandas |
| `export_excel.py` | rapport Excel avec OpenPyXL |
| `main.py` | ligne de commande : extraction, écriture en base, rapport |
| `app/main.py` | application FastAPI |
| `app/routes/` | routes de l'API : livres, catégories, extractions, santé |
| `app/schemas.py` | schémas Pydantic des paramètres et des réponses |
| `app/models.py` | tables SQLAlchemy : `categories`, `livres`, `extractions` |
| `app/depot.py` | tout le SQL : insertion ou mise à jour des livres, requêtes de lecture |
| `app/service_extraction.py` | déroulement d'une extraction et suivi de son statut |
| `app/config.py`, `app/db.py` | réglages par variables d'environnement, connexion à la base |
| `migrations/` | migrations Alembic |
| `Dockerfile`, `docker-compose.yml` | images de production et de test, services `db`, `api`, `db-tests`, `tests` |
| `tests/` | tests pytest |
| `docs/` | guide du projet et manuel utilisateur, en PDF |

## Choix techniques

- **Une seule extraction à la fois** : un index unique partiel sur `extractions` (`statut = 'en_cours'`) fait refuser le doublon par PostgreSQL lui-même, même si deux demandes arrivent au même instant.
- **Mise à jour sans doublon** : les livres sont écrits par `INSERT ... ON CONFLICT (url) DO UPDATE`.
- **Tâche de fond FastAPI** plutôt qu'une file de messages : suffisant pour une extraction à la fois. Une extraction coupée par l'arrêt de l'API est marquée `echouee` au démarrage suivant.
- **Extraction échouée** : aucun de ses livres n'est conservé, et l'erreur est lisible sur `GET /extractions/{id}`.
