"""Tests du moteur RAG multilingue et de l'outil search_tech_docs."""
from unittest.mock import MagicMock
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
    # Vérification des exigences de sécurité et de provenance (données non fiables)
    assert "data_notice" in res
    assert "non fiable" in res["data_notice"]
    assert top_match.get("trust") == "untrusted_document_data"


def test_idempotent_reindex_and_stale_chunks_purge(isolated_chroma):
    # Première indexation
    stats1 = rag.index_all_documents()
    assert stats1["files_indexed"] == 2
    collection = rag.get_collection()
    initial_count = collection.count()
    assert initial_count >= 2

    # Modification d'un fichier (raccourcissement)
    docs_file = isolated_chroma / "docs" / "maintenance_fr.md"
    docs_file.write_text("# Recalibrage court\nAttendre 5 min.", encoding="utf-8")

    # Suppression d'un autre fichier
    mat_file = isolated_chroma / "materials" / "fiches_techniques" / "huskylens_en.md"
    mat_file.unlink()

    # Réindexation : l'ancien fichier supprimé doit être purgé et le fichier modifié mis à jour
    stats2 = rag.index_all_documents()
    assert stats2["files_indexed"] == 1
    new_count = collection.count()
    # Il ne doit rester que les chunks du fichier maintenance_fr.md court
    assert new_count < initial_count
    records = collection.get(include=["metadatas"])
    sources_in_db = {m["source"] for m in records["metadatas"]}
    assert "materials/fiches_techniques/huskylens_en.md" not in sources_in_db
    assert "docs/maintenance_fr.md" in sources_in_db


def test_batching_upsert(isolated_chroma, monkeypatch):
    # Forcer un batch size très petit pour valider la boucle d'upsert par lots
    monkeypatch.setattr(rag, "_MAX_BATCH_SIZE", 1)
    stats = rag.index_all_documents(reset=True)
    assert stats["chunks_upserted"] >= 2
    collection = rag.get_collection()
    assert collection.count() == stats["chunks_upserted"]


def test_pdf_extraction_page_label(tmp_path, monkeypatch):
    dummy_pdf = tmp_path / "sample.pdf"
    dummy_pdf.touch()

    # Mock PdfReader pour simuler un PDF de 2 pages
    mock_reader = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = "Contenu Page 1"
    page2 = MagicMock()
    page2.extract_text.return_value = "Contenu Page 2"
    mock_reader.pages = [page1, page2]

    monkeypatch.setattr(rag, "PdfReader", lambda path: mock_reader)
    extracted = rag._extract_text(dummy_pdf)
    assert "[Page 1]\nContenu Page 1" in extracted
    assert "[Page 2]\nContenu Page 2" in extracted


def test_invalid_category_rejected():
    with pytest.raises(ValueError, match="category non autorisée"):
        tools.search_tech_docs(query="capteur", category="../../etc")


def test_rag_unavailable_graceful_handling(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if "factorypulse.agent.rag" in name:
            raise ImportError("No module named 'chromadb'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    res = tools.search_tech_docs("test")
    assert any("indisponible" in w for w in res["warnings"])
    assert res["matches"] == []


def test_sanitize_text_surrogates_and_null_bytes():
    # Surrogate pair (U+D835 U+DF16) -> U+1D716
    surrogate_pair = "\ud835\udf16"
    sanitized = rag._sanitize_text(surrogate_pair)
    assert sanitized == "\U0001d716"
    # Ensure it encodes cleanly to UTF-8
    assert sanitized.encode("utf-8") == b"\xf0\x9d\x9c\x96"

    # Lone surrogate (remplacé par \ufffd sans lever d'erreur UTF-8)
    lone_surrogate = "abc\ud835def"
    sanitized_lone = rag._sanitize_text(lone_surrogate)
    assert sanitized_lone == "abc\ufffddef"
    assert sanitized_lone.encode("utf-8") == b"abc\xef\xbf\xbddef"

    # Null bytes
    with_null = "sensor\x00data"
    assert rag._sanitize_text(with_null) == "sensordata"