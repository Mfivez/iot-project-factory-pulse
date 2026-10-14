# Conteneurisation du Serveur MCP FactoryPulse (avec RAG & ChromaDB)

Ce document décrit comment construire, exécuter et intégrer le **serveur MCP FactoryPulse** dans un conteneur Docker indépendant intégrant le moteur de recherche documentaire RAG multilingue sous ChromaDB.

---

## 1. Vue d'ensemble

Le serveur MCP (`factorypulse.agent.mcp_server`) expose six outils de diagnostic en lecture seule du laboratoire d'atelier :
- `get_status(station_id, at_utc)` : état synthétique d'une station à un instant du replay.
- `get_history(station_id, from_utc, to_utc)` : télémétries bornées dans un intervalle UTC.
- `get_logs(station_id, from_utc, to_utc)` : logs de la station et logs serveur la ciblant.
- `get_inspections(from_utc, to_utc)` : contrôles qualité Q01 dédupliqués.
- `get_latest_temperature_exceedance(at_utc)` : dernier dépassement de température configuré.
- `search_tech_docs(query, category=None, top_k=5)` : recherche sémantique multilingue dans la documentation technique (RAG ChromaDB).

### Principes de sécurité et d'isolation
- **Utilisateur non-root (`factorypulse:1000`)** : le conteneur s'exécute sans privilèges administrateur.
- **Lecture seule** : aucun accès en écriture sur les données de l'atelier, aucune commande shell ni accès réseau machine (conforme à `AGENTS.md`).
- **Isolation des données** : les fixtures de données (`data/fixtures`) et la configuration (`config/factorypulse.json`) sont montées en lecture seule (`:ro`).
- **Persistance vectorielle** : la base ChromaDB est isolée dans un volume persistant Docker (`chroma-data`), évitant les verrous de fichiers SQLite sur les systèmes de fichiers partagés Windows/WSL2.
- **100% Autonome & Offline** : le modèle multilingue SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`) est préchargé dans l'image lors du build Docker. Aucune connexion internet n'est requise à l'exécution.
- **Transports supportés** : `streamable-http` (par défaut sur le port TCP `8766`) et `stdio` (pour les clients exécutant directement le conteneur).

---

## 2. Fichiers créés et configurés

| Fichier | Rôle |
|---|---|
| `Dockerfile` | Image Debian-slim avec Python 3.11, PyTorch CPU, ChromaDB, SentenceTransformers, MCP, utilisateur non-root, préchargement du modèle et pré-indexation |
| `.dockerignore` | Exclusion des venvs, caches et fichiers temporaires tout en préservant `docs/` et `materials/` pour l'indexation RAG |
| `docker-compose.yml` | Orchestration avec volume persistant `chroma-data` et montages pour ré-indexation à chaud |
| `docs/DOCKER_MCP.md` | Ce guide d'utilisation et d'intégration |

---

## 3. Utilisation avec Docker Compose (Recommandé)

### 3.1. Démarrer le serveur
```bash
docker compose up -d --build
```

### 3.2. Vérifier le statut et les logs
```bash
docker compose ps
docker compose logs -f
```

### 3.3. Ré-indexer les documents techniques dans le conteneur
Si vous ajoutez ou modifiez des fichiers dans `docs/` ou `materials/` :
```bash
docker compose exec mcp-server python scripts/ingest_docs.py
```

### 3.4. Arrêter le serveur
```bash
docker compose down
```

---

## 4. Utilisation avec Docker CLI standard

### 4.1. Construction de l'image
```bash
docker build -t factorypulse-mcp-server:latest .
```

### 4.2. Lancement en mode réseau (Streamable-HTTP / TCP)
```bash
# Création du volume persistant pour ChromaDB
docker volume create chroma-data

# Lancement du conteneur avec fixtures, ChromaDB et documentation
docker run -d \
  --name factorypulse-mcp \
  -p 8766:8766 \
  -v ./config:/app/config:ro \
  -v ./data/fixtures:/app/data/fixtures:ro \
  -v chroma-data:/data/chromadb \
  -v ./docs:/app/docs:ro \
  -v ./materials:/app/materials:ro \
  factorypulse-mcp-server:latest
```

Le serveur écoute alors sur `http://127.0.0.1:8766/mcp`.

### 4.3. Lancement en mode `stdio` (via Docker CLI)
Pour les clients MCP qui communiquent via standard input/output :
```bash
docker run -i --rm \
  -e MCP_TRANSPORT=stdio \
  factorypulse-mcp-server:latest
```

---

## 5. Validation et Test de Connexion

Un script de test d'intégration est fourni dans le dépôt : [`tests/agent/test_mcp_tcp.py`](file:///c:/Users/j.bourdin/OneDrive/OneDrive%20-%20TechnofuturTIC/Documents/Dev/iot-project-factory-pulse/tests/agent/test_mcp_tcp.py).

Une fois le conteneur démarré, vous pouvez tester la connexion depuis votre machine hôte :

```bash
.venv/Scripts/python tests/agent/test_mcp_tcp.py
```

Si le conteneur tourne sur une autre machine ou un autre port :
```bash
# Exemple avec une URL personnalisée
MCP_URL=http://<IP_DU_SERVEUR>:8766/mcp .venv/Scripts/python tests/agent/test_mcp_tcp.py
```

Le test valide :
1. La connexion HTTP au serveur MCP.
2. La découverte de la liste des 6 outils (`get_status`, `get_history`, `get_logs`, `get_inspections`, `get_latest_temperature_exceedance`, `search_tech_docs`).
3. L'exécution réelle de l'outil `get_status(station_id='M01', at_utc='2026-10-12T09:00:02Z')`.
4. L'exécution d'une recherche documentaire RAG avec `search_tech_docs(query='contrat de données JSONL', top_k=3)`.

---

## 6. Configuration dans les Clients MCP (Assistants IA)

### 6.1. Claude Desktop ou VS Code (Transport HTTP / SSE)
Dans le fichier de configuration de votre client (ex: `claude_desktop_config.json`) :

```json
{
  "mcpServers": {
    "factorypulse": {
      "url": "http://127.0.0.1:8766/mcp"
    }
  }
}
```

### 6.2. Claude Desktop (Transport Stdio via Docker)
Si vous préférez que Claude lance automatiquement le conteneur à la demande :

```json
{
  "mcpServers": {
    "factorypulse": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT=stdio",
        "factorypulse-mcp-server:latest"
      ]
    }
  }
}
```

---

## 7. Variables d'environnement configurables

| Variable | Valeur par défaut dans Docker | Description |
|---|---|---|
| `MCP_TRANSPORT` | `streamable-http` | Protocole utilisé : `streamable-http`, `sse` ou `stdio` |
| `MCP_HOST` | `0.0.0.0` | Adresse d'écoute (obligatoire `0.0.0.0` dans le conteneur) |
| `MCP_PORT` | `8766` | Port TCP d'écoute du serveur HTTP |
| `FACTORYPULSE_ROOT`| `/app` | Chemin racine pour charger `config/`, `data/fixtures/` et les sources documentaires |
| `FACTORYPULSE_CHROMA_PATH` | `/data/chromadb` | Emplacement persistant de la base vectorielle ChromaDB |
| `HF_HOME` | `/opt/hf-cache` | Répertoire de stockage du modèle d'embedding SentenceTransformers préchargé |
| `HF_HUB_OFFLINE` | `1` | Verrouille HuggingFace en mode local (aucune requête réseau externe) |
| `TRANSFORMERS_OFFLINE` | `1` | Verrouille Transformers en mode local |
| `PYTHONUNBUFFERED` | `1` | Affiche immédiatement les logs sans mise en tampon |
