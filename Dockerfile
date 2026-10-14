# ==============================================================================
# Dockerfile - Serveur MCP FactoryPulse (Conteneur indépendant)
# ==============================================================================
# Image légère Python 3.11 basée sur Debian slim
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Equipe FactoryPulse"
LABEL description="Serveur MCP FactoryPulse en lecture seule pour le diagnostic atelier"
LABEL version="0.1.0"

# Variables d'environnement système et MCP
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FACTORYPULSE_ROOT=/app \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8766

# Création d'un utilisateur non-root pour respecter les principes de sécurité
# (Agent de diagnostic consultatif en lecture seule, sans privilèges root)
RUN groupadd -r factorypulse && useradd -r -g factorypulse -u 1000 -m factorypulse

WORKDIR /app

# Étape 1 : Installation des dépendances (mise en cache Docker optimale)
COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "mcp>=2.3.0"

# Étape 2 : Copie du code source et des fichiers nécessaires
COPY src/ /app/src/
COPY config/ /app/config/
COPY data/fixtures/ /app/data/fixtures/

# Installation du package FactoryPulse sans retélécharger de dépendances
RUN pip install --no-cache-dir --no-deps .

# Attribution des permissions à l'utilisateur non-root
RUN chown -R factorypulse:factorypulse /app

# Passage à l'utilisateur non privilégié
USER factorypulse

# Exposition du port TCP du serveur MCP
EXPOSE 8766

# Définition du Healthcheck réseau
HEALTHCHECK --interval=20s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.create_connection(('127.0.0.1', 8766), timeout=2); s.close()" || exit 1

# Commande de démarrage par défaut : lancement du serveur MCP
CMD ["python", "-m", "factorypulse.agent.mcp_server"]
