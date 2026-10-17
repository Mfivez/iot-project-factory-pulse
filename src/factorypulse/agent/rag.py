"""Moteur RAG multilingue sous ChromaDB pour la documentation FactoryPulse."""
from __future__ import annotations

import hashlib
import logging
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

from factorypulse.shared.paths import chroma_db_path, project_root, tech_doc_sources

# Réduire le niveau de log de pypdf pour éviter de saturer la console de warnings fontTools
logging.getLogger("pypdf").setLevel(logging.ERROR)

COLLECTION_NAME = "factorypulse_tech_docs"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
NVIDIA_MODEL = "nvidia/nemotron-3-embed-1b"
ALLOWED_CATEGORIES = frozenset(tech_doc_sources().keys())

_ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf", ".html", ".htm"}
_CHUNK_SIZE = 900  # caractères adaptés pour préserver paragraphes et sections complètes
_CHUNK_OVERLAP = 120
_MAX_BATCH_SIZE = 500  # limite de lot pour respecter ChromaDB / SQLite

# Singleton pour éviter de recharger le modèle à chaque appel d'outil MCP
_EMBEDDING_FN = None


class NvidiaEmbeddingFunction:
    """Fonction d'embedding en ligne via l'API NVIDIA NIM (OpenAI compatible).

    Offre 0% de charge CPU locale et des embeddings de haute qualité en cloud.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = NVIDIA_MODEL,
    ):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY requise pour NvidiaEmbeddingFunction")
        self.model_name = model_name
        self._url = "https://integrate.api.nvidia.com/v1/embeddings"
        self._session = httpx.Client(timeout=30.0)

    def _call_api(self, input_texts: list[str], input_type: str) -> list[list[float]]:
        batch_size = 32
        all_embeddings: list[list[float]] = []
        for i in range(0, len(input_texts), batch_size):
            batch = input_texts[i : i + batch_size]
            payload = {
                "input": batch,
                "model": self.model_name,
                "input_type": input_type,
            }
            response = self._session.post(
                self._url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            items = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
            all_embeddings.extend([item["embedding"] for item in items])
        return all_embeddings

    def __call__(self, input: list[str]) -> list[list[float]]:
        """Vectorise les passages documentaires lors de l'indexation."""
        return self._call_api(input, input_type="passage")

    def embed_query(self, input: list[str]) -> list[list[float]]:
        """Vectorise la question posée lors de la recherche."""
        return self._call_api(input, input_type="query")

    @staticmethod
    def name() -> str:
        return "nvidia"

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    def is_legacy(self) -> bool:
        return False

    def get_config(self) -> dict[str, Any]:
        return {"model_name": self.model_name}

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> NvidiaEmbeddingFunction:
        return NvidiaEmbeddingFunction(model_name=config.get("model_name", NVIDIA_MODEL))


def _sanitize_text(text: str) -> str:
    r"""Assainit le texte pour l'encodage UTF-8 et tokenizers (Rust).

    Recombine les paires de demi-surrogates UTF-16 issues de pypdf (ex: \ud835\udf16),
    élimine les octets nuls, supprime les icônes de la zone privée Unicode (ex: FontAwesome)
    et supprime les demi-surrogates isolés qui provoquent des erreurs de type.
    """
    if not text:
        return ""
    try:
        # Recombine les demi-surrogates consécutifs en caractères Unicode réels
        text = text.encode("utf-16", "surrogatepass").decode("utf-16", errors="replace")
    except Exception:
        pass
    text = text.replace("\x00", "")
    # Supprimer les caractères de la zone privée Unicode (ex: icônes Sphinx/FontAwesome \uf0c1)
    text = "".join(c for c in text if not (0xE000 <= ord(c) <= 0xF8FF))
    return text.encode("utf-8", "ignore").decode("utf-8")


def _get_embedding_fn():
    global _EMBEDDING_FN
    if _EMBEDDING_FN is not None:
        return _EMBEDDING_FN

    try:
        from factorypulse.agent.mcp_server import load_env_file
        load_env_file()
    except Exception:
        pass

    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        _EMBEDDING_FN = NvidiaEmbeddingFunction(api_key=nvidia_key)
        return _EMBEDDING_FN

    _EMBEDDING_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return _EMBEDDING_FN


def get_collection(reset: bool = False) -> chromadb.Collection:
    """Ouvre ou crée la collection ChromaDB persistante.

    Si reset=True ou si l'index HNSW existant est corrompu (ex: interruption
    d'écriture ou crash), supprime et recrée la collection proprement.
    """
    db_dir = chroma_db_path()
    db_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_dir))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    try:
        col = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embedding_fn(),
            metadata={"hnsw:space": "cosine"},
        )
        # Vérification de l'intégrité de l'index HNSW
        col.count()
        return col
    except Exception:
        # Récupération automatique en cas de corruption de segment HNSW
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embedding_fn(),
            metadata={"hnsw:space": "cosine"},
        )



class _HTMLTextExtractor(HTMLParser):
    """Extracteur de texte brut pour fichiers HTML ignorant scripts, styles et navigation."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "head", "meta", "link", "nav"}:
            self._skip = True
        elif tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "div", "section", "br"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "head", "meta", "link", "nav"}:
            self._skip = False
        elif tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "div", "section"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.text_parts.append(data)

    def get_text(self) -> str:
        return "".join(self.text_parts)


def _extract_text(file_path: Path) -> str:
    """Extrait le texte brut d'un fichier Markdown, Texte, PDF ou HTML."""
    suffix = file_path.suffix.lower()
    raw = ""
    if suffix in {".md", ".txt"}:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
    elif suffix in {".html", ".htm"}:
        parser = _HTMLTextExtractor()
        parser.feed(file_path.read_text(encoding="utf-8", errors="replace"))
        raw = parser.get_text()
    elif suffix == ".pdf":
        try:
            reader = PdfReader(str(file_path))
            pages_content = []
            for idx, page in enumerate(reader.pages):
                text = (page.extract_text() or "").strip()
                if text:
                    pages_content.append(f"[Page {idx + 1}]\n{text}")
            raw = "\n\n".join(pages_content)
        except Exception as exc:
            logging.warning("Échec de lecture du PDF %s : %s", file_path.name, exc)
            raw = ""
    return _sanitize_text(raw)



def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Découpe le texte en respectant prioritairement les titres Markdown et paragraphes."""
    clean_text = _sanitize_text(text).strip()
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
            # Si un bloc isolé dépasse chunk_size, découpage par phrases propres
            if len(block) > chunk_size:
                sentences = re.split(r"(?<=[.!?\n])\s+", block)
                sub_curr = ""
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    if len(sub_curr) + len(s) + 1 <= chunk_size:
                        sub_curr = f"{sub_curr} {s}" if sub_curr else s
                    else:
                        if sub_curr:
                            chunks.append(sub_curr)
                        sub_curr = s
                if sub_curr:
                    chunks.append(sub_curr)
                current = ""
            else:
                tail = current[-overlap:] if len(current) > overlap else current
                current = f"{tail}\n\n{block}".strip() if tail else block

    if current:
        chunks.append(current)
    return [_sanitize_text(c) for c in chunks if _sanitize_text(c).strip()]



def index_all_documents(reset: bool = False) -> dict[str, int]:
    """Parcourt les dossiers autorisés et indexe les documents de façon idempotente."""
    collection = get_collection(reset=reset)
    root = project_root()
    sources = tech_doc_sources()


    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    files_processed = 0
    active_sources: set[str] = set()

    for category, folder in sources.items():
        if not folder.exists():
            continue
        for file_path in sorted(folder.rglob("*")):
            if not file_path.is_file() or file_path.suffix.lower() not in _ALLOWED_EXTENSIONS:
                continue
            if file_path.name == ".gitkeep":
                continue

            rel_path = file_path.relative_to(root).as_posix()
            active_sources.add(rel_path)
            text = _extract_text(file_path)
            chunks = _chunk_text(text)
            if not chunks:
                try:
                    collection.delete(where={"source": rel_path})
                except Exception:
                    pass
                continue

            # Purge préventive des anciens chunks de ce fichier pour éviter les orphelins
            try:
                collection.delete(where={"source": rel_path})
            except Exception:
                pass

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

    # Nettoyage des sources orphelines présentes dans ChromaDB mais supprimées du disque
    if not reset:
        try:
            existing_records = collection.get(include=["metadatas"])
            stale_sources = {
                meta["source"]
                for meta in (existing_records.get("metadatas") or [])
                if meta and "source" in meta and meta["source"] not in active_sources
            }
            for stale_source in stale_sources:
                collection.delete(where={"source": stale_source})
        except Exception:
            pass

    # Upsert par lots pour respecter les plafonds de requêtes ChromaDB / SQLite
    for i in range(0, len(ids), _MAX_BATCH_SIZE):
        collection.upsert(
            ids=ids[i : i + _MAX_BATCH_SIZE],
            documents=documents[i : i + _MAX_BATCH_SIZE],
            metadatas=metadatas[i : i + _MAX_BATCH_SIZE],
        )

    return {"files_indexed": files_processed, "chunks_upserted": len(ids)}