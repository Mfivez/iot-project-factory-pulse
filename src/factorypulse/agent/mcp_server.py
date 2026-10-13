"""Serveur MCP local en stdio pour les outils de diagnostic FactoryPulse."""

from mcp.server import MCPServer

from factorypulse.agent import tools


# FastMCP gère le protocole MCP et la communication stdio avec le client.
# Le nom est celui que Codex ou Claude affichera dans sa liste de serveurs.
mcp = MCPServer("factorypulse-readonly", version="0.1.0")


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
    # stdio signifie que le client MCP lance ce processus et échange avec lui
    # sur stdin/stdout; aucun serveur HTTP ni port réseau n'est ouvert.
    mcp.run(transport="stdio")
