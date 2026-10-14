# Conteneurisation du Serveur MCP FactoryPulse

Ce document décrit comment construire, exécuter et intégrer le **serveur MCP FactoryPulse** dans un conteneur Docker indépendant.

---

## 1. Vue d'ensemble

Le serveur MCP (`factorypulse.agent.mcp_server`) expose les outils de diagnostic en lecture seule du laboratoire d'atelier :
- `get_status(station_id, at_utc)`
- `get_history(station_id, from_utc, to_utc)`
- `get_logs(station_id, from_utc, to_utc)`
- `get_inspections(from_utc, to_utc)`
- `get_latest_temperature_exceedance(at_utc)`

### Principes de sécurité et d'isolation
- **Utilisateur non-root (`factorypulse:1000`)** : le conteneur s'exécute sans privilèges administrateur.
- **Lecture seule** : aucun accès en écriture, aucune commande shell ni accès réseau machine (conforme à `AGENTS.md`).
- **Données montées en lecture seule (`:ro`)** : les fixtures de données (`data/fixtures`) et la configuration (`config/factorypulse.json`) restent isolées.
- **Transports supportés** : `streamable-http` (par défaut sur le port TCP `8766`) et `stdio` (pour les clients exécutant directement le conteneur).

---

## 2. Fichiers créés

| Fichier | Rôle |
|---|---|
| `Dockerfile` | Image Debian-slim multi-architecture avec Python 3.11, dépendance `mcp`, utilisateur non-root et healthcheck |
| `.dockerignore` | Exclusion des venvs, caches, tests et fichiers non nécessaires pour une image légère et propre |
| `docker-compose.yml` | Fichier d'orchestration pour lancer le conteneur en une seule commande |
| `docs/DOCKER_MCP.md` | Ce guide d'utilisation et d'intégration |

---

## 3. Utilisation avec Docker Compose (Recommandé)

### Démarrer le serveur
```bash
docker compose up -d --build
```

### Vérifier le statut et les logs
```bash
docker compose ps
docker compose logs -f
```

### Arrêter le serveur
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
docker run -d \
  --name factorypulse-mcp \
  -p 8766:8766 \
  -v ./config:/app/config:ro \
  -v ./data/fixtures:/app/data/fixtures:ro \
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
2. La découverte de la liste des 5 outils.
3. L'exécution réelle de l'outil `get_status(station_id='M01', at_utc='2026-10-12T09:00:02Z')`.

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
| `FACTORYPULSE_ROOT`| `/app` | Chemin racine pour charger `config/` et `data/fixtures/` |
| `PYTHONUNBUFFERED` | `1` | Affiche immédiatement les logs sans mise en tampon |
