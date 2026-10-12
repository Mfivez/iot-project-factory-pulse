import copy
import pytest
from factorypulse.shared.contracts import validate_event, parse_utc, ContractError
from factorypulse.shared.jsonl import read_jsonl, dedupe_events, write_jsonl
from factorypulse.shared.paths import fixture_path


def test_all_fixtures_respect_contract():
    for name in ("m01.jsonl", "q01.jsonl", "systeme.jsonl", "logs.jsonl"):
        assert read_jsonl(fixture_path(name))


def test_q01_contains_exact_duplicate_not_seventh_part():
    events = read_jsonl(fixture_path("q01.jsonl"))
    assert len(events) == 7
    assert len(dedupe_events(events)) == 6


def test_conflicting_duplicate_rejected():
    base = read_jsonl(fixture_path("q01.jsonl"))[0]
    different = copy.deepcopy(base)
    different["payload"]["verdict"] = "REJECT"
    with pytest.raises(ContractError, match="Collision"):
        dedupe_events([base, different])


def test_missing_temperature_is_valid_null():
    base = copy.deepcopy(read_jsonl(fixture_path("m01.jsonl"))[0])
    base["payload"]["temperature_c"] = None
    base["payload"]["data_quality"] = "TEMPERATURE_MISSING"
    base["payload"]["alert_level"] = "DATA_ISSUE"
    assert validate_event(base) is base


def test_invalid_timestamp_rejected():
    with pytest.raises(ContractError):
        parse_utc("2026-10-12T09:00:00")


def test_invalid_confidence_rejected():
    base = copy.deepcopy(read_jsonl(fixture_path("q01.jsonl"))[0])
    base["payload"]["confidence"] = 1.5
    with pytest.raises(ContractError, match="confidence"):
        validate_event(base)


def test_roundtrip_jsonl(tmp_path):
    originals = read_jsonl(fixture_path("q01.jsonl"))[:2]
    target = tmp_path / "sample.jsonl"
    write_jsonl(originals, target)
    assert read_jsonl(target) == originals
