"""Tests d'intégration du client MCP sur transport réseau (SSE ou streamable-http).

Ces tests supposent que le serveur MCP est DÉJÀ démarré. Ils sont ignorés
automatiquement si aucun serveur n'écoute sur l'hôte/port configuré.
Pour démarrer le serveur :
    .venv/Scripts/python -m factorypulse.agent.mcp_server

Attention : un autre processus (ex. conteneur Docker) écoutant sur le même port
peut répondre à la place du serveur local. Vérifier qu'un seul serveur écoute.

Les tests asynchrones utilisent le plugin pytest fourni par ``anyio``
(dépendance de ``mcp``), sans dépendance supplémentaire.
"""
import json
import os
import socket
import sys
from contextlib import asynccontextmanager

import pytest

from factorypulse.agent.mcp_server import get_mcp_config


EXPECTED_TOOLS = {
    "get_status",
    "get_history",
    "get_logs",
    "get_inspections",
    "get_latest_temperature_exceedance",
    "search_tech_docs",
}


def _client_config() -> dict:
    """Lit la configuration MCP (.env inclus) sans polluer os.environ des autres tests."""
    saved_env = os.environ.copy()
    try:
        config = get_mcp_config(load_env=True)
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    # 0.0.0.0 est une adresse d'écoute serveur ; le client local se connecte sur 127.0.0.1
    host = config["host"]
    client_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
    path = "/sse" if config["transport"] == "sse" else "/mcp"
    default_url = f"http://{client_host}:{config['port']}{path}"
    return {
        **config,
        "client_host": client_host,
        "url": os.getenv("MCP_URL", default_url),
    }


def _port_is_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Indique si un processus accepte des connexions TCP sur host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


CONFIG = _client_config()

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.skipif(
        CONFIG["transport"] == "stdio",
        reason="MCP_TRANSPORT=stdio : pas de serveur réseau à tester",
    ),
    pytest.mark.skipif(
        CONFIG["transport"] != "stdio"
        and not _port_is_open(CONFIG["client_host"], CONFIG["port"]),
        reason=f"Aucun serveur MCP n'écoute sur {CONFIG['client_host']}:{CONFIG['port']}",
    ),
]


@pytest.fixture
def anyio_backend():
    """Limite les tests anyio au backend asyncio (trio n'est pas installé)."""
    return "asyncio"


@asynccontextmanager
async def _connect():
    """Ouvre une session client MCP selon le transport configuré."""
    from mcp.client import Client

    if CONFIG["transport"] == "sse":
        from mcp.client.sse import sse_client

        target = sse_client(CONFIG["url"])
    else:
        target = CONFIG["url"]

    async with Client(server=target) as client:
        yield client


def _json_result(result) -> dict:
    """Vérifie qu'un appel d'outil a réussi et décode sa réponse JSON."""
    assert not result.is_error, f"L'outil a renvoyé une erreur : {result.content[0].text}"
    assert result.content, "Réponse d'outil vide"
    return json.loads(result.content[0].text)


async def test_server_exposes_expected_tools():
    async with _connect() as client:
        tools_result = await client.list_tools()

    tool_names = {tool.name for tool in tools_result.tools}
    missing = EXPECTED_TOOLS - tool_names
    assert not missing, (
        f"Outils absents sur {CONFIG['url']} : {sorted(missing)}. "
        f"Outils trouvés : {sorted(tool_names)}. "
        "Un autre serveur (ex. ancienne image Docker) répond-il sur ce port ?"
    )


async def test_get_status_returns_replay_summary():
    async with _connect() as client:
        result = await client.call_tool(
            "get_status",
            arguments={"station_id": "M01", "at_utc": "2026-10-12T09:00:02Z"},
        )

    data = _json_result(result)
    assert data["as_of_utc"] == "2026-10-12T09:00:02Z"
    assert set(data["summary"]) == {"node_state", "machine_state", "data_age_s"}
    assert isinstance(data["events"], list)
    assert isinstance(data["warnings"], list)


async def test_search_tech_docs_returns_structured_response():
    # La base ChromaDB peut être vide : l'outil doit alors répondre proprement
    # avec un avertissement plutôt qu'une erreur.
    async with _connect() as client:
        result = await client.call_tool(
            "search_tech_docs",
            arguments={"query": "contrat de données JSONL", "top_k": 3},
        )

    data = _json_result(result)
    assert data["query"] == "contrat de données JSONL"
    assert isinstance(data["matches"], list)
    assert len(data["matches"]) <= 3
    assert isinstance(data["warnings"], list)
    if not data["matches"]:
        assert data["warnings"], "Aucun résultat et aucun avertissement explicatif"
    for match in data["matches"]:
        assert match["source"], "Chaque extrait doit indiquer sa source (preuve)"
        assert match["content"]


async def test_invalid_station_is_rejected():
    async with _connect() as client:
        result = await client.call_tool(
            "get_status",
            arguments={"station_id": "../../etc", "at_utc": "2026-10-12T09:00:02Z"},
        )

    assert result.is_error, "Une station non autorisée doit être refusée"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-rs"]))
