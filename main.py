"""Chaîne complète : extraction web (Playwright) -> traitement (Pandas) -> rapport Excel (OpenPyXL)."""

import argparse
import sys
import time
from pathlib import Path

from export_excel import exporter
from extraction import ExtracteurCatalogue
from traitement import indicateurs_par_categorie, nettoyer


def lire_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--navigateur", choices=["chrome", "msedge", "chromium"], default="chrome",
                        help="chrome ou msedge déjà présent sur le poste, ou chromium (installé par Playwright)")
    parser.add_argument("--visible", action="store_true",
                        help="affiche la fenêtre du navigateur pendant l'extraction")
    parser.add_argument("--max-categories", type=int, default=None,
                        help="limite le nombre de catégories parcourues (pour un essai rapide)")
    parser.add_argument("--sortie", default="sortie", help="dossier des fichiers générés")
    return parser.parse_args()


def main() -> None:
    args = lire_arguments()
    dossier = Path(args.sortie)
    dossier.mkdir(parents=True, exist_ok=True)
    debut = time.perf_counter()

    extracteur = ExtracteurCatalogue(args.navigateur, args.visible, args.max_categories)
    livres = extracteur.extraire()
    if not livres:
        sys.exit("Aucun livre extrait : la structure du site a peut-être changé.")

    df = nettoyer(livres)
    kpi = indicateurs_par_categorie(df)

    # utf-8-sig : Excel ouvre le CSV avec les accents corrects.
    df.to_csv(dossier / "catalogue.csv", index=False, encoding="utf-8-sig")
    exporter(df, kpi, dossier / "rapport_catalogue.xlsx")

    duree = time.perf_counter() - debut
    print(f"{len(df)} livres, {len(kpi)} catégories, {duree:.0f} s. Fichiers dans : {dossier.resolve()}")


if __name__ == "__main__":
    main()
