"""RGAP registry integrity tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATHS = (
    Path("data/satcom/source_register.yaml"),
    Path("data/satcom/published/source_register.yaml"),
)

MANDATORY_ADMITTED_FIELDS = (
    "artifact_id",
    "title",
    "authors",
    "publisher",
    "source_url",
    "retrieved_utc",
    "sha256",
    "licence",
    "scientific_layer",
    "transformation_history",
    "uncertainty_notes",
)

INVALID_HASHES = {
    "",
    "null",
    "placeholder",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    with path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    if payload is None:
        return []
    if not isinstance(payload, dict):
        raise AssertionError(f"Registry {path} must use the schema envelope mapping")

    artifacts = payload.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise AssertionError(f"Registry {path} field 'artifacts' must be a list")

    records: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise AssertionError(f"Registry {path} contains a non-mapping artifact")
        record = dict(artifact)
        record["__source_file"] = str(path)
        records.append(record)
    return records


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def test_admitted_records_satisfy_guardrails() -> None:
    records = [record for path in REGISTRY_PATHS for record in _load_records(path)]

    for record in records:
        if record.get("admission_state") != "ADMITTED":
            continue

        artifact_id = str(record.get("artifact_id", "UNKNOWN_ID"))
        source_file = record.get("__source_file")

        for field in MANDATORY_ADMITTED_FIELDS:
            assert not _is_blank(record.get(field)), (
                f"RGAP guardrail failure in {source_file}: admitted artifact "
                f"'{artifact_id}' has a missing or blank '{field}' field"
            )

        sha256 = str(record["sha256"]).strip().lower()
        assert sha256 not in INVALID_HASHES, (
            f"RGAP guardrail failure in {source_file}: admitted artifact "
            f"'{artifact_id}' contains a placeholder SHA-256"
        )
        assert len(sha256) == 64, (
            f"RGAP guardrail failure in {source_file}: admitted artifact "
            f"'{artifact_id}' SHA-256 must contain exactly 64 hexadecimal characters"
        )
        assert all(character in "0123456789abcdef" for character in sha256), (
            f"RGAP guardrail failure in {source_file}: admitted artifact "
            f"'{artifact_id}' SHA-256 is not hexadecimal"
        )
