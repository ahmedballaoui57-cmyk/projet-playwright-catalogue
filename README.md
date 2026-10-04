# Extraction de catalogue web : Playwright, Pandas, OpenPyXL

Script Python qui automatise une chaîne complète d'extraction, de traitement et de chargement de données :

1. **Extraction** (Playwright) : ouvre un navigateur, parcourt les 50 catégories de [books.toscrape.com](https://books.toscrape.com/) en suivant la pagination, et collecte environ 1 000 livres (titre, prix, note, disponibilité).
2. **Traitement** (Pandas) : nettoie les textes bruts (prix, notes), supprime les doublons et calcule des indicateurs par catégorie.
3. **Chargement** (OpenPyXL) : génère un rapport Excel mis en forme (en-têtes, filtres, formats, graphique) et un fichier CSV.

Le site cible est un site d'entraînement public, conçu pour être extrait.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Le script pilote le Chrome déjà installé sur le poste : aucun navigateur à télécharger.

## Utilisation

```bash
python main.py
```

Options :

| Option | Effet |
|---|---|
| `--max-categories 3` | essai rapide sur 3 catégories |
| `--visible` | affiche le navigateur pendant l'extraction |
| `--navigateur msedge` | utilise Edge à la place de Chrome |
| `--navigateur chromium` | utilise le Chromium de Playwright (après `playwright install chromium`) |
| `--sortie dossier` | dossier des fichiers générés (par défaut `sortie`) |

## Résultat

- `sortie/rapport_catalogue.xlsx` : feuille **Indicateurs** (nombre de livres, prix moyen, minimum, maximum et note moyenne par catégorie, avec graphique) et feuille **Catalogue** (toutes les lignes, filtrables).
- `sortie/catalogue.csv` : les données nettoyées.

## Tests et intégration continue

Les trois étapes sont couvertes par des tests automatisés (pytest), sans accès au réseau :

```bash
pip install -r requirements-dev.txt
pytest
```

Les tests d'extraction lancent un vrai navigateur sur une copie miniature du site (`tests/site/`), servie en local. Ils utilisent le Chrome du poste ; pour utiliser le Chromium de Playwright à la place :

```bash
set NAVIGATEUR_TESTS=chromium
pytest
```

À chaque envoi de code sur GitHub, le workflow `.github/workflows/tests.yml` (GitHub Actions) installe les dépendances et le Chromium de Playwright, puis relance ces tests.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `extraction.py` | classe `ExtracteurCatalogue` : navigation, pagination, lecture des pages |
| `traitement.py` | nettoyage et indicateurs avec Pandas |
| `export_excel.py` | rapport Excel avec OpenPyXL |
| `main.py` | enchaîne les trois étapes, lit les options de la ligne de commande |
| `tests/` | tests pytest de l'extraction, du traitement et de l'export Excel |
| `.github/workflows/tests.yml` | intégration continue avec GitHub Actions |
