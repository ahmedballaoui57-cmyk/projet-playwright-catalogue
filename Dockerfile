FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NAVIGATEUR=chromium

# L'application ne tourne pas en root.
RUN useradd --create-home appli
WORKDIR /app

# Dépendances avant le code : cette couche reste en cache tant que requirements.txt ne change pas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY alembic.ini main.py extraction.py traitement.py export_excel.py ./
COPY migrations migrations
COPY app app
RUN mkdir sortie && chown appli /app sortie


# Image des tests : le code de production, plus pytest et le dossier tests/.
FROM base AS tests
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY pytest.ini .
COPY tests tests
USER appli
CMD ["pytest", "-v"]


# Image de production (cible par défaut) : applique les migrations puis lance l'API.
FROM base AS prod
USER appli
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
