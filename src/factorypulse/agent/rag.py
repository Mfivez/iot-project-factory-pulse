"""Moteur RAG multilingue sous ChromaDB pour la documentation FactoryPulse."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

from factorypulse.shared.paths import chroma_db_path, project_root, tech_doc_sources

COLLECTION_NAME = "factorypulse_tech_docs"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
ALLOWED_CATEGORIES = frozenset(tech_doc_sources().keys())

_ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}
_CHUNK_SIZE = 1200  # caractères (~250-300 tokens)
_CHUNK_OVERLAP = 200

# Singleton pour éviter de recharger le modèle PyTorch à chaque appel d'outil MCP
_EMBEDDING_FN = None


def _get_embedding_fn():
    global _EMBEDDING_FN
    if _EMBEDDING_FN is None:
        _EMBEDDING_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
    return _EMBEDDING_FN


def get_collection() -> chromadb.Collection:
    """Ouvre ou crée la collection ChromaDB persistante."""
    db_dir = chroma_db_path()
    db_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_dir))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def _extract_text(file_path: Path) -> str:
    """Extrait le texte brut d'un fichier Markdown, Texte ou PDF."""
    suffix = file_path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return file_path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    return ""


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Découpe le texte en respectant prioritairement les titres Markdown et paragraphes."""
    clean_text = text.strip()
    if not clean_text:
        return []

    # Découpage sur les titres Markdown ou doubles sauts de ligne
    blocks = re.split(r"(?=\n#{1,3}\s)|\n\s*\n", clean_text)
    chunks: list[str] = []
    current = ""

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if len(current) + len(block) + 2 <= chunk_size:
            current = f"{current}\n\n{block}" if current else block
        else:
            if current:
                chunks.append(current)
            # Si un bloc isolé dépasse chunk_size, découpage glissant
            if len(block) > chunk_size:
                step = max(1, chunk_size - overlap)
                for i in range(0, len(block), step):
                    chunks.append(block[i : i + chunk_size])
                current = ""
            else:
                tail = current[-overlap:] if len(current) > overlap else current
                current = f"{tail}\n\n{block}".strip() if tail else block

    if current:
        chunks.append(current)
    return chunks


def index_all_documents() -> dict[str, int]:
    """Parcourt les dossiers autorisés et indexe les documents de façon idempotente."""
    collection = get_collection()
    root = project_root()
    sources = tech_doc_sources()

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    files_processed = 0

    for category, folder in sources.items():
        if not folder.exists():
            continue
        for file_path in sorted(folder.rglob("*")):
            if not file_path.is_file() or file_path.suffix.lower() not in _ALLOWED_EXTENSIONS:
                continue
            if file_path.name == ".gitkeep":
                continue

            rel_path = file_path.relative_to(root).as_posix()
            text = _extract_text(file_path)
            chunks = _chunk_text(text)
            if not chunks:
                continue

            files_processed += 1
            for idx, chunk in enumerate(chunks):
                chunk_hash = hashlib.sha256(f"{rel_path}::{idx}".encode("utf-8")).hexdigest()[:16]
                chunk_id = f"doc_{chunk_hash}"
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append({
                    "source": rel_path,
                    "filename": file_path.name,
                    "category": category,
                    "chunk_index": idx,
                })

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    return {"files_indexed": files_processed, "chunks_upserted": len(ids)}