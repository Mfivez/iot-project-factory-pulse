"""Test client MCP - Validation de la connexion et des outils.

Ce test suppose que le serveur MCP est DÉJÀ démarré sur 127.0.0.1:8766.
Pour démarrer le serveur :
    .venv/Scripts/python -m factorypulse.agent.mcp_server
"""
import os
import sys
import asyncio
import json

import pytest


from factorypulse.agent.mcp_server import get_mcp_config


@pytest.mark.skip(reason="Test d'intégration nécessitant un serveur MCP démarré")
async def test_mcp_client_connection():
    """Teste la connexion client MCP et l'appel d'un outil."""
    config = get_mcp_config(load_env=True)
    transport = config["transport"]
    host = config["host"]
    port = config["port"]

    # 0.0.0.0 est une adresse d'écoute serveur ; le client local doit se connecter sur 127.0.0.1
    client_host = "127.0.0.1" if host in ("0.0.0.0", "") else host

    if transport == "sse":
        default_url = f"http://{client_host}:{port}/sse"
    else:
        default_url = f"http://{client_host}:{port}/mcp"

    server_url = os.getenv("MCP_URL", default_url)

    print("=" * 60)
    print(f"TEST: Client MCP (cible: {server_url}, transport: {transport})")
    print("=" * 60)
    
    try:
        from mcp.client import Client
        if transport == "sse":
            from mcp.client.sse import sse_client
    except ImportError as e:
        print(f"[ERREUR] Bibliothèques manquantes: {e}")
        print("Installez avec: .venv/Scripts/pip install mcp")
        return False
    
    try:
        # 1. Connexion au serveur MCP (avec async context manager)
        print(f"[1/3] Connexion au serveur MCP ({server_url})...")
        server_target = sse_client(server_url) if transport == "sse" else server_url
        async with Client(server=server_target) as client:
            print("    [OK] Connexion établie")
            
            # 2. Lister les outils disponibles
            print("[2/3] Liste des outils disponibles...")
            tools_result = await client.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            print(f"    [OK] Outils trouvés: {tool_names}")
            
            if "get_status" not in tool_names:
                print("    [ERREUR] L'outil 'get_status' n'est pas disponible")
                return False
            
            # 3. Appeler l'outil get_status avec une date valide du replay
            print("[3/3] Appel de get_status(station_id='M01', at_utc='2026-10-12T09:00:02Z')...")
            result = await client.call_tool(
                "get_status",
                arguments={"station_id": "M01", "at_utc": "2026-10-12T09:00:02Z"}
            )
            
            print(f"    [OK] Appel réussi")
            if result.is_error:
                print(f"    [ERREUR] Le serveur a renvoyé une erreur : {result.content[0].text}")
                return False

            data = json.loads(result.content[0].text)
            print(f"    as_of_utc: {data.get('as_of_utc', 'N/A')}")
            print(f"    summary: {data.get('summary', {})}")
            
            return True
        
    except ConnectionError as e:
        print(f"[ERREUR] Impossible de se connecter au serveur MCP: {e}")
        print("Assurez-vous que le serveur est démarré:")
        print("    .venv/Scripts/python -m factorypulse.agent.mcp_server")
        return False
    except Exception as e:
        print(f"[ERREUR] Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if not asyncio.run(test_mcp_client_connection()):
        print("\n[FAILED] Test échoué")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Test client MCP passé !")
        sys.exit(0)
