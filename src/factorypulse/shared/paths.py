"""Localisation des ressources du dépôt en mode atelier."""
import os
from pathlib import Path


def project_root() -> Path:
    """Racine du dépôt ; configurable pour les tests/outils d'intégration."""
    override = os.environ.get("FACTORYPULSE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[3]


def fixture_path(filename: str) -> Path:
    """Réserve la lecture aux quatre fichiers d'exemple autorisés."""
    permitted = {"m01.jsonl", "q01.jsonl", "systeme.jsonl", "logs.jsonl"}
    if filename not in permitted:
        raise ValueError(f"Nom de fixture interdit : {filename!r}")
    return project_root() / "data" / "fixtures" / filename


def chroma_db_path() -> Path:
    """Emplacement persistant de la base vectorielle ChromaDB."""
    override = os.environ.get("FACTORYPULSE_CHROMA_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return project_root() / "data" / "chromadb"


def tech_doc_sources() -> dict[str, Path]:
    """Répertoires de documentation technique autorisés pour l'indexation RAG."""
    root = project_root()
    return {
        "docs": root / "docs",
        "fiches_materiel": root / "materials" / "fiches_materiel",
        "fiches_techniques": root / "materials" / "fiches_techniques",
        "montages": root / "materials" / "montages",
        "essais": root / "materials" / "essais",
        "modeles": root / "materials" / "modeles",
        "vision": root / "src" / "factorypulse" / "vision",
    }