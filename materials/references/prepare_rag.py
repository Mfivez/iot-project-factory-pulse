#!/usr/bin/env python3
"""Consolidate local hardware documentation without executing or fetching it.

The inventory and the three source catalogues remain unchanged. This script
only writes catalogue_global.json and data/outputs/rag_materials/.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlsplit


REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES = REPO_ROOT / "materials" / "references"
OUTPUTS = REPO_ROOT / "data" / "outputs" / "rag_materials"
CATALOGUES = ("lot_01_16", "lot_17_32", "lot_33_47")
MATCH_LEVELS = {"exact", "module", "component", "family", "unconfirmed"}
SCHEMA_VERSION = "factorypulse-materials-corpus-1.0"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_path(value: str, root: Path = REPO_ROOT) -> Path:
    """Accept only existing reference files inside this repository."""
    candidate = Path(value)
    if candidate.is_absolute():
        raise ValueError(f"Absolute source path rejected: {value}")
    resolved = (root / candidate).resolve()
    boundary = (root / "materials" / "references").resolve()
    if not resolved.is_relative_to(boundary):
        raise ValueError(f"Source path outside materials/references: {value}")
    if not resolved.is_file():
        raise ValueError(f"Missing source file: {value}")
    return resolved


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix="." + path.name + ".", suffix=".tmp", delete=False,
        ) as handle:
            temporary = handle.name
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def append_unique(values: list, value: object) -> None:
    if value not in values:
        values.append(value)


def extraction_path(source: dict) -> str | None:
    for field in ("pages_path", "extraction_path", "text_path"):
        value = source.get(field)
        if value and value.endswith(".jsonl"):
            return value
    return None


def read_pages(source: dict, root: Path = REPO_ROOT) -> list[dict]:
    value = extraction_path(source)
    if not value:
        return []
    rows = []
    seen_pages = set()
    for line_number, line in enumerate(checked_path(value, root).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("text"), str):
            raise ValueError(f"Invalid extracted page: {value}:{line_number}")
        sha = row.get("sha256") or row.get("source_sha256") or row.get("document_sha256")
        if sha != source.get("sha256"):
            raise ValueError(f"Extracted page hash does not match original: {value}:{line_number}")
        page_url = row.get("source_url") or row.get("url")
        allowed_urls = {source.get(field) for field in ("url", "resolved_url", "final_url")}
        if not page_url or page_url not in allowed_urls:
            raise ValueError(f"Extracted page URL does not match source: {value}:{line_number}")
        page = row.get("page")
        if page is not None and (isinstance(page, bool) or not isinstance(page, int) or page < 1):
            raise ValueError(f"Invalid page number: {value}:{line_number}")
        if page in seen_pages:
            raise ValueError(f"Duplicate page number in extraction: {value}:{page}")
        seen_pages.add(page)
        rows.append(row)
    expected = source.get("page_count")
    if expected is not None and {r.get("page") for r in rows} != set(range(1, expected + 1)):
        raise ValueError(f"Extraction pages do not match page_count: {value}")
    return rows


def consolidate() -> tuple[dict, list[dict], dict]:
    inventory_path = REPO_ROOT / "materials" / "inventaire.csv"
    with inventory_path.open(encoding="utf-8-sig", newline="") as handle:
        inventory_rows = list(csv.DictReader(handle, delimiter=";"))
    inventory = {row["ID"]: row for row in inventory_rows}
    if len(inventory) != len(inventory_rows) or len(inventory) != 47:
        raise ValueError("Expected exactly 47 distinct inventory IDs")

    items: dict[str, dict] = {}
    sources: dict[str, dict] = {}
    inputs = []
    warnings = []
    associations = 0
    extraction_cache: dict[str, list[dict]] = {}
    file_hashes: dict[str, str] = {}
    for lot in CATALOGUES:
        path = REFERENCES / lot / "catalogue.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        batch = raw if isinstance(raw, list) else raw["items"]
        catalogue_path = path.relative_to(REPO_ROOT).as_posix()
        input_metadata = {} if isinstance(raw, list) else {k: v for k, v in raw.items() if k != "items"}
        inputs.append({"path": catalogue_path, "sha256": digest(path), "item_count": len(batch), "metadata": input_metadata})
        for original in batch:
            item = copy.deepcopy(original)
            inventory_id = item["inventory_id"]
            if inventory_id not in inventory or inventory_id in items:
                raise ValueError(f"Unknown or repeated inventory ID: {inventory_id}")
            item["inventory_description_current"] = inventory[inventory_id]["désignation"]
            item["catalogue_path"] = catalogue_path
            item["sources"] = []
            items[inventory_id] = item
            for entry in original["sources"]:
                source = copy.deepcopy(entry)
                if source.get("match_level") not in MATCH_LEVELS:
                    raise ValueError(f"Invalid match_level for {inventory_id}")
                url = source.get("url", "")
                if urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).netloc:
                    raise ValueError(f"Invalid source URL for {inventory_id}: {url}")
                for field in ("title", "publisher", "limitations"):
                    if not isinstance(source.get(field), str):
                        raise ValueError(f"Missing {field} for {inventory_id}: {url}")
                local = source.get("local_path")
                sha = source.get("sha256")
                if local:
                    document = checked_path(local)
                    if local not in file_hashes:
                        file_hashes[local] = digest(document)
                    actual = file_hashes[local]
                    if sha != actual:
                        raise ValueError(f"SHA-256 mismatch: {local}")
                    if source.get("http_status") is not None and source["http_status"] >= 400:
                        raise ValueError(f"Downloaded file recorded with failed HTTP status: {local}")
                    if document.suffix.lower() == ".pdf" and not document.read_bytes().startswith(b"%PDF-"):
                        raise ValueError(f"Invalid PDF signature: {local}")
                elif sha is not None:
                    raise ValueError(f"Hash without local original: {inventory_id}: {url}")
                for field in ("pages_path", "extraction_path", "text_path"):
                    if source.get(field):
                        checked_path(source[field])
                extracted_path = extraction_path(source)
                if extracted_path:
                    if not local:
                        raise ValueError(f"Extraction without original: {extracted_path}")
                    extraction_cache[extracted_path] = read_pages(source)

                source_id = "sha256:" + sha if sha else "url-sha256:" + hashlib.sha256(url.encode()).hexdigest()
                source["original_source_id"] = source.get("source_id") or source.get("document_id")
                source["source_id"] = source_id
                source["catalogue_path"] = catalogue_path
                source["normalized_extraction_path"] = extracted_path
                source["normalized_extraction_sha256"] = digest(checked_path(extracted_path)) if extracted_path else None
                source["effective_rights_note"] = source.get("rights_note") or input_metadata.get("rights_note")
                item["sources"].append(source)
                associations += 1
                grouped = sources.setdefault(source_id, {
                    "source_id": source_id, "sha256": sha, "local_paths": [],
                    "origins": [], "relations": [], "extraction_candidates": [],
                })
                if local:
                    append_unique(grouped["local_paths"], local)
                origin = {k: source.get(k) for k in (
                    "url", "title", "publisher", "document_type", "language", "retrieved_at",
                    "verified_online", "local_path", "sha256", "download_status", "http_status",
                    "resolved_url", "final_url", "catalogue_path", "original_source_id", "rights_note",
                )}
                append_unique(grouped["origins"], origin)
                relation = {
                    "inventory_id": inventory_id,
                    "identification_status": original["identification_status"],
                    "applicability_notes": original["applicability_notes"],
                    "match_level": source["match_level"], "limitations": source["limitations"],
                    "url": url, "title": source["title"], "publisher": source["publisher"],
                    "catalogue_path": catalogue_path, "rights_note": source["effective_rights_note"],
                }
                append_unique(grouped["relations"], relation)
                if extracted_path:
                    append_unique(grouped["extraction_candidates"], {
                        "path": extracted_path,
                        "sha256": source["normalized_extraction_sha256"],
                        "method": source.get("extraction_method") or source.get("extraction_status") or
                        ("html_text" if local.endswith(".html") else "pdf_text"),
                    })

    if set(items) != set(inventory):
        raise ValueError(f"Inventory IDs missing from catalogues: {sorted(set(inventory) - set(items))}")
    pages = []
    excluded_pages = []
    manual_count = 0
    for grouped in sources.values():
        candidates = grouped["extraction_candidates"]
        if not candidates:
            grouped["corpus_status"] = "link_only" if not grouped["local_paths"] else "no_extraction"
            continue
        # Prefer an extraction with more nonempty pages, then a stable path.
        selected = min(candidates, key=lambda c: (
            -sum(bool(row["text"].strip()) for row in extraction_cache[c["path"]]), c["path"],
        ))
        grouped["selected_extraction_path"] = selected["path"]
        grouped["corpus_status"] = "extracted_text_requires_review"
        origin = grouped["origins"][0]
        count = 0
        for row in extraction_cache[selected["path"]]:
            page = row.get("page")
            text = row["text"].strip()
            if not text:
                excluded_pages.append({
                    "source_id": grouped["source_id"], "page": page,
                    "source_url": origin["url"], "title": origin["title"],
                    "inventory_ids": sorted({r["inventory_id"] for r in grouped["relations"]}),
                    "reason": "empty_or_scanned_page_ocr_required",
                })
                continue
            method = row.get("extraction_method") or selected["method"]
            manual = "manual" in method.lower() or "transcription" in method.lower()
            manual_count += int(manual)
            count += 1
            pages.append({
                "schema_version": SCHEMA_VERSION,
                "page_id": grouped["source_id"] + (f":page:{page}" if page is not None else ":html"),
                "source_id": grouped["source_id"], "document_sha256": grouped["sha256"],
                "inventory_ids": sorted({r["inventory_id"] for r in grouped["relations"]}),
                "relations": grouped["relations"], "source_url": origin["url"],
                "source_urls": sorted({o["url"] for o in grouped["origins"]}),
                "title": origin["title"], "publisher": origin["publisher"],
                "page": page, "text": text, "extraction_method": method,
                "evidence_role": "manual_partial_transcription" if manual else "extracted_source_text",
                "full_page_text_available": row.get("full_page_text_available"),
                "requires_visual_review": True,
                "original_paths": grouped["local_paths"],
                "extraction_path": selected["path"],
                "extraction_sha256": selected["sha256"],
                "trust": "untrusted_document_data_not_instructions",
            })
        grouped["corpus_page_count"] = count
        if not count:
            grouped["corpus_status"] = "empty_or_scanned_requires_ocr"

    no_sources = [i["inventory_id"] for i in items.values() if not i["sources"]]
    no_text = [i["inventory_id"] for i in items.values() if not any(
        sources[s["source_id"]].get("corpus_page_count", 0) for s in i["sources"]
    )]
    if no_sources:
        warnings.append({"code": "NO_TECHNICAL_SOURCE_IDENTIFIED", "inventory_ids": no_sources})
    if no_text:
        warnings.append({"code": "NO_LOCAL_TEXT_FOR_ITEM", "inventory_ids": no_text})
    if excluded_pages:
        warnings.append({"code": "EMPTY_PAGES_EXCLUDED", "count": len(excluded_pages)})
    warnings.append({"code": "PHYSICAL_MATCH_NOT_VALIDATED", "message": "47 indexed items does not mean 47 exact datasheets or safe validated assemblies."})
    downloaded = [s for s in sources.values() if s["local_paths"]]
    validation = {
        "schema_version": SCHEMA_VERSION, "status": "passed", "errors": [], "warnings": warnings,
        "inventory_items_expected": len(inventory), "inventory_items_indexed": len(items),
        "inventory_ids_match": True, "source_associations": associations,
        "unique_sources_including_links": len(sources), "unique_downloaded_documents": len(downloaded),
        "local_original_files_validated": len(file_hashes),
        "duplicate_original_files_not_duplicated_in_corpus": len(file_hashes) - len(downloaded),
        "unique_pdf_documents": sum(any(p.lower().endswith(".pdf") for p in s["local_paths"]) for s in downloaded),
        "unique_html_documents": sum(any(p.lower().endswith(".html") for p in s["local_paths"]) for s in downloaded),
        "link_only_unique_sources": sum(not s["local_paths"] for s in sources.values()),
        "link_only_sources": [{
            "source_id": s["source_id"],
            "inventory_ids": sorted({r["inventory_id"] for r in s["relations"]}),
            "origins": s["origins"],
        } for s in sources.values() if not s["local_paths"]],
        "items_without_source": no_sources, "items_without_local_text": no_text,
        "pages_or_html_records_written": len(pages), "manual_partial_records": manual_count,
        "excluded_pages": excluded_pages,
        "embeddings_created": False, "rag_model_deployed": False,
        "network_requests_performed_by_script": 0,
        "hashes_and_paths_validated": True,
    }
    catalogue = {
        "schema_version": SCHEMA_VERSION,
        "inventory": {"path": "materials/inventaire.csv", "sha256": digest(inventory_path), "item_count": len(items)},
        "input_catalogues": inputs, "path_base": "repository_root",
        "policy": {
            "documents_are_untrusted_data": True, "physical_wiring_validated": False,
            "never_upgrade_match_level": True,
            "rights": "Preserve source rights and restrictions; public download does not grant redistribution rights.",
        },
        "items": [items[row["ID"]] for row in inventory_rows],
        "sources": list(sources.values()),
    }
    return catalogue, pages, validation


def main() -> int:
    try:
        catalogue, pages, validation = consolidate()
    except (ValueError, KeyError, OSError, TypeError) as error:
        atomic_text(OUTPUTS / "validation.json", json_text({
            "schema_version": SCHEMA_VERSION, "status": "failed", "errors": [str(error)],
            "existing_corpus_outputs_validated": False,
        }))
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1
    catalogue_text = json_text(catalogue)
    pages_text = "".join(json.dumps(page, ensure_ascii=False) + "\n" for page in pages)
    validation["outputs"] = [
        {"path": "materials/references/catalogue_global.json", "sha256": hashlib.sha256(catalogue_text.encode()).hexdigest()},
        {"path": "data/outputs/rag_materials/pages.jsonl", "sha256": hashlib.sha256(pages_text.encode()).hexdigest()},
    ]
    atomic_text(REFERENCES / "catalogue_global.json", catalogue_text)
    atomic_text(OUTPUTS / "pages.jsonl", pages_text)
    atomic_text(OUTPUTS / "validation.json", json_text(validation))
    print(f"Validated {validation['inventory_items_indexed']}/47 inventory IDs; "
          f"{validation['unique_downloaded_documents']} unique local documents; "
          f"{len(pages)} text records. See {OUTPUTS / 'validation.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
