"""Test client MCP - Validation de la connexion et des outils.

Ce test suppose que le serveur MCP est DÉJÀ démarré sur 127.0.0.1:8766.
Pour démarrer le serveur :
    .venv/Scripts/python -m factorypulse.agent.mcp_server
"""
import sys
import asyncio


async def test_mcp_client_connection():
    """Teste la connexion client MCP et l'appel d'un outil."""
    print("=" * 60)
    print("TEST: Client MCP (serveur doit être démarré sur 127.0.0.1:8766)")
    print("=" * 60)
    
    try:
        from mcp.client import Client
    except ImportError as e:
        print(f"[ERREUR] Bibliothèques manquantes: {e}")
        print("Installez avec: .venv/Scripts/pip install mcp")
        return False
    
    try:
        # 1. Connexion au serveur MCP (avec async context manager)
        print("[1/3] Connexion au serveur MCP (127.0.0.1:8766)...")
        async with Client(server="http://127.0.0.1:8766/mcp") as client:
            print("    [OK] Connexion établie")
            
            # 2. Lister les outils disponibles
            print("[2/3] Liste des outils disponibles...")
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            print(f"    [OK] Outils trouvés: {tool_names}")
            
            if "get_status" not in tool_names:
                print("    [ERREUR] L'outil 'get_status' n'est pas disponible")
                return False
            
            # 3. Appeler l'outil get_status
            print("[3/3] Appel de get_status(station_id='M01', at_utc='2024-01-15T10:00:00Z')...")
            result = await client.call_tool(
                "get_status",
                arguments={"station_id": "M01", "at_utc": "2024-01-15T10:00:00Z"}
            )
            
            print(f"    [OK] Appel réussi")
            print(f"    as_of_utc: {result.get('as_of_utc', 'N/A')}")
            print(f"    summary: {result.get('summary', {})}")
            
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
