"""Serveur MCP pour les outils de diagnostic FactoryPulse.

Support des transports stdio (par défaut) et streamable-http (TCP/IP).
Configurable via variables d'environnement MCP_TRANSPORT, MCP_HOST, MCP_PORT.
"""

import os
from pathlib import Path

from mcp.server import MCPServer

from factorypulse.agent import tools


# FastMCP gère le protocole MCP et la communication avec le client.
# Le nom est celui que Codex ou Claude affichera dans sa liste de serveurs.
mcp = MCPServer("factorypulse-readonly", version="0.1.0")


def load_env_file(env_path: Path | str | None = None, override: bool = False) -> dict[str, str]:
    """Charge les variables d'un fichier .env dans os.environ sans dépendance externe.

    Par défaut, ne remplace pas les variables d'environnement déjà existantes (override=False).
    """
    if env_path is None:
        try:
            from factorypulse.shared.paths import project_root
            resolved_path = project_root() / ".env"
        except Exception:
            resolved_path = Path(__file__).resolve().parents[3] / ".env"
    else:
        resolved_path = Path(env_path)

    if not resolved_path.is_file():
        resolved_path = Path(".env")
    if not resolved_path.is_file():
        return {}

    loaded = {}
    try:
        with resolved_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if not (val.startswith('"') or val.startswith("'")):
                    if " #" in val:
                        val = val.split(" #", 1)[0].strip()
                    elif "\t#" in val:
                        val = val.split("\t#", 1)[0].strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                loaded[key] = val
                if override or key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass
    return loaded


# Configuration du transport via variables d'environnement
def get_mcp_config(load_env: bool = False, env_path: Path | str | None = None) -> dict:
    """Lire la configuration MCP depuis les variables d'environnement.
    les valeurs par défaut sont:
        MCP_TRANSPORT=streamable-http
        MCP_HOST=127.0.0.1
        MCP_PORT=8766
    """
    if load_env:
        load_env_file(env_path=env_path)
    transport = os.getenv("MCP_TRANSPORT", "streamable-http").strip().lower()
    host = os.getenv("MCP_HOST", "127.0.0.1").strip()
    port_str = os.getenv("MCP_PORT", "8766").strip()
    
    # Validation basique
    valid_transports = ("stdio", "sse", "streamable-http")
    if transport not in valid_transports:
        raise ValueError(
            f"MCP_TRANSPORT doit être 'stdio', 'sse' ou 'streamable-http', "
            f"got: {transport!r}"
        )
    
    # Validation du port
    try:
        port = int(port_str)
        if not (0 < port <= 65535):
            raise ValueError(f"MCP_PORT doit être un nombre entre 1 et 65535, got: {port}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"MCP_PORT doit être un entier valide: {e}") from e
    
    return {
        "transport": transport,
        "host": host,
        "port": port,
    }


@mcp.tool()
def get_status(station_id: str, at_utc: str) -> dict:
    """Lire le dernier état connu de la machine et du nœud à un instant du replay."""
    return tools.get_status(station_id, at_utc)


@mcp.tool()
def get_history(station_id: str, from_utc: str, to_utc: str) -> dict:
    """Lire les télémétries de la station dans un intervalle UTC inclusif."""
    return tools.get_history(station_id, from_utc, to_utc)


@mcp.tool()
def get_logs(station_id: str, from_utc: str, to_utc: str) -> dict:
    """Lire les logs de la station et les logs serveur qui la ciblent."""
    return tools.get_logs(station_id, from_utc, to_utc)


@mcp.tool()
def get_inspections(from_utc: str, to_utc: str) -> dict:
    """Lire les inspections Q01 uniques dans un intervalle UTC inclusif."""
    return tools.get_inspections(from_utc, to_utc)


@mcp.tool()
def get_latest_temperature_exceedance(at_utc: str) -> dict:
    """Trouver le dépassement de température configuré le plus récent jusqu'à at_utc."""
    return tools.get_latest_temperature_exceedance(at_utc)


if __name__ == "__main__":
    config = get_mcp_config(load_env=True)
    transport = config["transport"]
    
    if transport == "stdio":
        # stdio signifie que le client MCP lance ce processus et échange avec lui
        # sur stdin/stdout; aucun serveur HTTP ni port réseau n'est ouvert.
        print("[MCP] Server \"factorypulse-readonly\" (v0.1.0) ready on stdio.", flush=True)
        mcp.run(transport="stdio")
    elif transport == "streamable-http":
        # Mode TCP/IP: le serveur écoute sur host:port
        host = config["host"]
        port = config["port"]
        msg = f'[MCP] Server "factorypulse-readonly" (v0.1.0) ready on http://{host}:{port}/mcp'
        print(msg, flush=True)
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
        )
    elif transport == "sse":
        # Mode SSE (Server-Sent Events)
        host = config["host"]
        port = config["port"]
        msg = f'[MCP] Server "factorypulse-readonly" (v0.1.0) ready on http://{host}:{port}'
        print(msg, flush=True)
        mcp.run(
            transport="sse",
            host=host,
            port=port
        )
