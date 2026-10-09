"""Réglages lus dans les variables d'environnement (ou un fichier .env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Reglages(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://catalogue:catalogue@localhost:5432/catalogue"
    # Exigée dans l'en-tête X-API-Key pour lancer une extraction.
    cle_api: str = "changez-moi"
    # chrome ou msedge déjà présent sur le poste, ou chromium (installé par Playwright).
    navigateur: str = "chrome"


reglages = Reglages()
