"""Nettoyage des données extraites et calcul des indicateurs avec Pandas."""

import pandas as pd

# Le site écrit la note en toutes lettres dans une classe CSS ("star-rating Three").
NOTES = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

COLONNES = ["categorie", "titre", "prix_gbp", "note", "en_stock", "url"]


def nettoyer(livres: list[dict]) -> pd.DataFrame:
    """Transforme les textes bruts du site en colonnes typées."""
    df = pd.DataFrame(livres)
    # "£51.77" -> 51.77 (on ne garde que les chiffres et le point)
    df["prix_gbp"] = df["prix"].str.replace(r"[^\d.]", "", regex=True).astype(float)
    df["note"] = df["note"].map(NOTES)
    df["en_stock"] = df["disponibilite"].str.contains("In stock")
    df = df.drop_duplicates(subset="url")
    return df[COLONNES].sort_values(["categorie", "titre"]).reset_index(drop=True)


def indicateurs_par_categorie(df: pd.DataFrame) -> pd.DataFrame:
    """Un indicateur par catégorie, les plus fournies en premier."""
    kpi = df.groupby("categorie").agg(
        nb_livres=("titre", "count"),
        prix_moyen=("prix_gbp", "mean"),
        prix_min=("prix_gbp", "min"),
        prix_max=("prix_gbp", "max"),
        note_moyenne=("note", "mean"),
    )
    kpi = kpi.round(2).sort_values("nb_livres", ascending=False)
    return kpi.reset_index()
