"""Chaîne complète : extraction web (Playwright) -> traitement (Pandas) -> PostgreSQL et rapport Excel."""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

from app.config import reglages
from app.db import SessionLocale
from app.service_extraction import AUCUN_LIVRE, ExtractionDejaEnCours, demarrer, executer
from export_excel import exporter
from extraction import ExtracteurCatalogue
from traitement import indicateurs_par_categorie, nettoyer


def lire_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--navigateur", choices=["chrome", "msedge", "chromium"],
                        default=reglages.navigateur,
                        help="chrome ou msedge déjà présent sur le poste, ou chromium (installé par Playwright)")
    parser.add_argument("--visible", action="store_true",
                        help="affiche la fenêtre du navigateur pendant l'extraction")
    parser.add_argument("--max-categories", type=int, default=None,
                        help="limite le nombre de catégories parcourues (pour un essai rapide)")
    parser.add_argument("--sortie", default="sortie", help="dossier des fichiers générés")
    parser.add_argument("--sans-base", action="store_true",
                        help="n'écrit pas dans PostgreSQL : seuls les fichiers sont générés")
    return parser.parse_args()


def extraire_vers_base(extracteur: ExtracteurCatalogue) -> pd.DataFrame:
    with SessionLocale() as session:
        try:
            extraction = demarrer(session)
        except ExtractionDejaEnCours:
            sys.exit("Une extraction est déjà en cours.")
    try:
        return executer(extraction.id, extracteur)
    except Exception as erreur:
        sys.exit(f"Extraction échouée : {erreur}")


def extraire_sans_base(extracteur: ExtracteurCatalogue) -> pd.DataFrame:
    livres = extracteur.extraire()
    if not livres:
        sys.exit(AUCUN_LIVRE)
    return nettoyer(livres)


def main() -> None:
    args = lire_arguments()
    dossier = Path(args.sortie)
    dossier.mkdir(parents=True, exist_ok=True)
    debut = time.perf_counter()

    extracteur = ExtracteurCatalogue(args.navigateur, args.visible, args.max_categories)
    df = extraire_sans_base(extracteur) if args.sans_base else extraire_vers_base(extracteur)
    kpi = indicateurs_par_categorie(df)

    # utf-8-sig : Excel ouvre le CSV avec les accents corrects.
    df.to_csv(dossier / "catalogue.csv", index=False, encoding="utf-8-sig")
    exporter(df, kpi, dossier / "rapport_catalogue.xlsx")

    duree = time.perf_counter() - debut
    print(f"{len(df)} livres, {len(kpi)} catégories, {duree:.0f} s. Fichiers dans : {dossier.resolve()}")


if __name__ == "__main__":
    main()
