"""Client interactif en ligne de commande pour interroger le serveur RAG FactoryPulse (via MCP).

Usage interactif :
    python scripts/query_rag.py

Usage avec requête directe :
    python scripts/query_rag.py "quelle est la procédure en cas de surchauffe"
    python scripts/query_rag.py "HuskyLens voltage" --top-k 3
    python scripts/query_rag.py "ESP8266" --category references

Options :
    --top-k N       Nombre d'extraits souhaités (défaut: 3, max: 20)
    --category CAT  Filtrer par catégorie (docs, fiches_materiel, fiches_techniques, montages, essais, modeles, references, vision)
    --url URL       URL personnalisée du serveur MCP (défaut: déduit du .env)
    --direct        Mode direct local (interroge ChromaDB sans passer par le serveur réseau MCP)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

# Forcer la sortie UTF-8 sur Windows PowerShell / CMD
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Réduire le bruit des logs réseau HTTP/SSE et des bibliothèques tierces
logging.disable(logging.INFO)
logging.getLogger("pypdf").setLevel(logging.ERROR)

from factorypulse.agent.mcp_server import get_mcp_config


def _resolve_client_target(custom_url: str | None = None) -> tuple[str, str]:
    """Détermine l'URL et le type de transport à utiliser pour contacter le serveur MCP."""
    if custom_url:
        transport = "sse" if "/sse" in custom_url else "streamable-http"
        return custom_url, transport

    config = get_mcp_config(load_env=True)
    host = config["host"]
    client_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
    transport = config["transport"]
    path = "/sse" if transport == "sse" else "/mcp"
    url = os.getenv("MCP_URL", f"http://{client_host}:{config['port']}{path}")
    return url, transport


@asynccontextmanager
async def _connect_client(url: str, transport: str):
    """Ouvre une session avec le serveur MCP selon le transport (SSE ou Streamable-HTTP)."""
    from mcp.client import Client

    if transport == "sse":
        from mcp.client.sse import sse_client
        target = sse_client(url)
    else:
        target = url

    async with Client(server=target) as client:
        yield client


async def execute_rag_query_mcp(
    query: str,
    url: str,
    transport: str,
    category: str | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """Envoie une requête RAG au serveur MCP distant ou local et retourne la réponse."""
    async with _connect_client(url, transport) as client:
        result = await client.call_tool(
            "search_tech_docs",
            arguments={"query": query, "category": category, "top_k": top_k},
        )
        if result.is_error:
            error_msg = result.content[0].text if result.content else "Erreur inconnue"
            raise RuntimeError(f"Erreur renvoyée par le serveur : {error_msg}")
        return json.loads(result.content[0].text)


def execute_rag_query_direct(
    query: str,
    category: str | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """Interroge directement le moteur RAG local sans passer par le serveur réseau."""
    from factorypulse.agent import tools
    return tools.search_tech_docs(query=query, category=category, top_k=top_k)


def display_results(data: dict[str, Any], mode_label: str = "Serveur MCP") -> None:
    """Affiche les résultats retournés par le RAG de façon claire et lisible."""
    print("\n" + "=" * 70)
    print(f"  RÉSULTATS [{mode_label}] pour : \"{data.get('query')}\"")
    if data.get("category"):
        print(f"  Filtre catégorie : {data.get('category')}")
    print("=" * 70)

    # Avertissement de sécurité (règle AGENTS.md : données non fiables)
    notice = data.get("data_notice")
    if notice:
        print(f"\n[SÉCURITÉ] {notice}")

    warnings = data.get("warnings") or []
    for w in warnings:
        print(f"  [Avertissement] {w}")

    matches = data.get("matches") or []
    if not matches:
        print("\n  Aucun extrait documentaire pertinent trouvé.")
        print("=" * 70)
        return

    print(f"\n  {len(matches)} extrait(s) trouvé(s) :\n")
    for idx, match in enumerate(matches, 1):
        score = match.get("similarity_score", 0.0)
        source = match.get("source", "N/A")
        cat = match.get("category", "N/A")
        chunk_idx = match.get("chunk_index", 0)
        content = match.get("content", "").strip()

        print(f"  [{idx}] Source : {source}  |  Catégorie : {cat}  |  Bloc #{chunk_idx}")
        print(f"      Score de similarité : {score:.4f} ({score * 100:.1f}%)")
        print("      " + "-" * 55)
        for line in content.splitlines():
            print(f"      | {line}")
        print("      " + "-" * 55 + "\n")
    print("=" * 70)


async def interactive_loop(
    url: str,
    transport: str,
    default_top_k: int = 3,
    category: str | None = None,
    direct_mode: bool = False,
) -> None:
    """Boucle interactive en ligne de commande invitant l'utilisateur à saisir ses requêtes."""
    mode_label = "Direct Local" if direct_mode else f"Serveur MCP ({url})"
    print("=" * 70)
    print("  CLIENT INTERACTIF DE TEST RAG - FACTORYPULSE")
    print(f"  Mode : {mode_label}")
    if category:
        print(f"  Catégorie active : {category}")
    print("  Commandes :")
    print("    - Tapez n'importe quelle question ou mot-clé")
    print("    - Tapez ':cat <nom>' pour changer de catégorie (ou ':cat all' pour tout chercher)")
    print("    - Tapez 'q' ou 'exit' pour quitter")
    print("=" * 70)

    current_category = category

    while True:
        try:
            prompt_str = f"\n[RAG{f':{current_category}' if current_category else ''}] > "
            query = input(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSortie du client.")
            break

        if not query:
            continue
        if query.lower() in ("q", "quit", "exit"):
            print("Fermeture du client.")
            break
        if query.startswith(":cat"):
            parts = query.split(maxsplit=1)
            if len(parts) > 1:
                target_cat = parts[1].strip()
                current_category = None if target_cat.lower() in ("all", "none", "*") else target_cat
                print(f"-> Filtre catégorie mis à jour : {current_category or 'toutes'}")
            else:
                print(f"-> Catégorie actuelle : {current_category or 'toutes'}")
            continue

        try:
            if direct_mode:
                data = execute_rag_query_direct(
                    query=query,
                    category=current_category,
                    top_k=default_top_k,
                )
            else:
                data = await execute_rag_query_mcp(
                    query=query,
                    url=url,
                    transport=transport,
                    category=current_category,
                    top_k=default_top_k,
                )
            display_results(data, mode_label=mode_label)
        except Exception as exc:
            print(f"\n[ERREUR] Impossible d'interroger le serveur : {exc}")
            if not direct_mode:
                print("Conseil : assurez-vous que le serveur MCP écoute (ex: docker compose up ou python -m factorypulse.agent.mcp_server).")
                print("Vous pouvez également tester en mode local direct avec l'option --direct.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Client de test en ligne de commande pour interroger le serveur RAG FactoryPulse."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Question ou terme technique facultatif. Si omis, démarre en mode interactif.",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="URL du serveur MCP (ex: http://127.0.0.1:8766/sse). Déduite du .env par défaut.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Nombre maximal d'extraits documentaires à remonter (défaut: 3).",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Filtrer par catégorie (docs, fiches_materiel, fiches_techniques, montages, etc.).",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Interroge directement ChromaDB en local sans passer par le serveur réseau MCP.",
    )

    args = parser.parse_args()
    url, transport = _resolve_client_target(args.url)

    if args.query:
        # Mode une seule requête directe
        try:
            if args.direct:
                data = execute_rag_query_direct(
                    query=args.query,
                    category=args.category,
                    top_k=args.top_k,
                )
                mode_label = "Direct Local"
            else:
                data = asyncio.run(
                    execute_rag_query_mcp(
                        query=args.query,
                        url=url,
                        transport=transport,
                        category=args.category,
                        top_k=args.top_k,
                    )
                )
                mode_label = f"Serveur MCP ({url})"
            display_results(data, mode_label=mode_label)
        except Exception as exc:
            print(f"[ERREUR] Échec de la requête RAG : {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        # Mode interactif
        asyncio.run(
            interactive_loop(
                url=url,
                transport=transport,
                default_top_k=args.top_k,
                category=args.category,
                direct_mode=args.direct,
            )
        )


if __name__ == "__main__":
    main()
