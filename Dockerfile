# ==============================================================================
# Dockerfile - Serveur MCP FactoryPulse (Conteneur indépendant avec RAG & ChromaDB)
# ==============================================================================
# Image légère Python 3.11 basée sur Debian slim
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Equipe FactoryPulse"
LABEL description="Serveur MCP FactoryPulse en lecture seule pour le diagnostic atelier (outils fixtures + RAG documentation)"
LABEL version="0.2.0"

# Modèle d'embedding multilingue par défaut (doit correspondre à rag.EMBEDDING_MODEL)
ARG EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Variables d'environnement système, MCP et RAG
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FACTORYPULSE_ROOT=/app \
    FACTORYPULSE_CHROMA_PATH=/data/chromadb \
    HF_HOME=/opt/hf-cache \
    HF_HUB_DISABLE_TELEMETRY=1 \
    ANONYMIZED_TELEMETRY=False \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8766

# Création d'un utilisateur non-root pour respecter les principes de sécurité
# (Agent de diagnostic consultatif en lecture seule, sans privilèges root)
RUN groupadd -r factorypulse && useradd -r -g factorypulse -u 1000 -m factorypulse

WORKDIR /app

# Étape 1 : Installation des dépendances (mise en cache Docker optimale)
# PyTorch CPU dédié pour limiter la taille de l'image (~180 Mo au lieu de ~900 Mo avec CUDA)
COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch && \
    pip install --no-cache-dir \
        "mcp>=2.3.0" \
        "chromadb>=1.5.9" \
        "pypdf>=6.20.1" \
        "sentence-transformers>=6.1.0"

# Étape 2 : Préchargement du modèle HuggingFace pour un conteneur 100% autonome et offline
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')" && \
    chown -R factorypulse:factorypulse /opt/hf-cache

# Verrouillage du mode offline après le téléchargement initial
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

# Étape 3 : Copie du code source, de la configuration, des fixtures et de la documentation technique
COPY src/ /app/src/
COPY config/ /app/config/
COPY data/fixtures/ /app/data/fixtures/
COPY docs/ /app/docs/
COPY materials/ /app/materials/
COPY scripts/ /app/scripts/

# Installation du package FactoryPulse sans retélécharger de dépendances et validation du modèle
RUN pip install --no-cache-dir --no-deps . && \
    python -c "from factorypulse.agent import rag; assert rag.EMBEDDING_MODEL == '${EMBEDDING_MODEL}', 'EMBEDDING_MODEL du Dockerfile différent de rag.py'"

# Étape 4 : Création du dossier ChromaDB, indexation initiale des documents et attribution des droits
RUN mkdir -p /data/chromadb && \
    python scripts/ingest_docs.py && \
    chown -R factorypulse:factorypulse /app /data

# Passage à l'utilisateur non privilégié
USER factorypulse

# Exposition du port TCP du serveur MCP
EXPOSE 8766

# Définition du Healthcheck réseau (start-period de 60s adapté à l'initialisation du modèle et du serveur)
HEALTHCHECK --interval=20s --timeout=3s --start-period=60s --retries=3 \
    CMD python -c "import socket; s = socket.create_connection(('127.0.0.1', 8766), timeout=2); s.close()" || exit 1

# Commande de démarrage par défaut : lancement du serveur MCP
CMD ["python", "-m", "factorypulse.agent.mcp_server"]

