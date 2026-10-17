"""Script d'indexation de la documentation technique dans ChromaDB."""
import sys
from factorypulse.agent.rag import index_all_documents
from factorypulse.shared.paths import chroma_db_path


def main() -> None:
    reset = "--reset" in sys.argv
    print(f"[RAG] Indexation vers : {chroma_db_path()} (reset={reset})")
    stats = index_all_documents(reset=reset)
    print(
        f"[RAG] Terminé : {stats['files_indexed']} fichier(s) lu(s), "
        f"{stats['chunks_upserted']} segment(s) indexé(s)."
    )


if __name__ == "__main__":
    main()