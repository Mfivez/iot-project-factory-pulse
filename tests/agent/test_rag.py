"""Tests du moteur RAG multilingue et de l'outil search_tech_docs."""
import pytest
from factorypulse.agent import rag, tools


@pytest.fixture()
def isolated_chroma(tmp_path, monkeypatch):
    """Isole ChromaDB et les sources documentaires dans un dossier temporaire."""
    chroma_dir = tmp_path / "chromadb"
    docs_dir = tmp_path / "docs"
    mat_dir = tmp_path / "materials" / "fiches_techniques"
    docs_dir.mkdir(parents=True)
    mat_dir.mkdir(parents=True)

    # Fiche technique en anglais
    (mat_dir / "huskylens_en.md").write_text(
        "# HuskyLens Pro Vision Sensor\n\n"
        "Operating voltage: 3.3V to 5.0V DC. Current consumption: 320mA at 3.3V.\n"
        "Interfaces supported: UART (9600-115200 bps) and I2C (address 0x32).",
        encoding="utf-8",
    )
    # Procédure en français
    (docs_dir / "maintenance_fr.md").write_text(
        "# Procédure de recalibrage M01\n\n"
        "En cas de dépassement thermique au-dessus de 80 °C, couper l'alimentation "
        "et attendre 15 minutes avant de relancer le capteur d'accélération.",
        encoding="utf-8",
    )

    monkeypatch.setenv("FACTORYPULSE_CHROMA_PATH", str(chroma_dir))
    monkeypatch.setattr(rag, "project_root", lambda: tmp_path)
    monkeypatch.setattr(
        rag,
        "tech_doc_sources",
        lambda: {"docs": docs_dir, "fiches_techniques": mat_dir},
    )
    return tmp_path


def test_multilingual_rag_search(isolated_chroma):
    stats = rag.index_all_documents()
    assert stats["files_indexed"] == 2
    assert stats["chunks_upserted"] >= 2

    # Requête en français ciblant une donnée présente uniquement dans la doc en anglais
    res = tools.search_tech_docs(
        query="Quelle est la tension d'alimentation et l'adresse I2C de la caméra HuskyLens ?",
        top_k=2,
    )
    assert res["warnings"] == []
    assert len(res["matches"]) >= 1
    top_match = res["matches"][0]
    assert top_match["filename"] == "huskylens_en.md"
    assert "0x32" in top_match["content"]


def test_invalid_category_rejected():
    with pytest.raises(ValueError, match="category non autorisée"):
        tools.search_tech_docs(query="capteur", category="../../etc")