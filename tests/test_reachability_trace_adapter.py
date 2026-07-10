"""Tests for the structural L1.4 reachability trace adapter."""

import json
import math
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.aircraft.envelope import (
    ControlBounds,
    ReachabilityRequest,
    evaluate_reachability,
)
from mh370_inverse_inference.aircraft.state import AircraftState
from mh370_inverse_inference.aircraft.trace_adapter import ReachabilityTraceAdapter
from mh370_inverse_inference.engine.hashing import compose_step_hash

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "trace"
    / "reachability_trace_001.expected.json"
)
SHA256_PLACEHOLDER = "<sha256>"


def build_summary():
    request = ReachabilityRequest(
        initial_state=AircraftState(
            timestamp_utc="2014-03-08T18:22:00Z",
            latitude_deg=0.0,
            longitude_deg=0.0,
            altitude_m=10000.0,
            true_airspeed_mps=200.0,
            heading_deg=90.0,
            mass_kg=200000.0,
            model_version="aircraft-dynamics-1.0.0",
        ),
        control_bounds=ControlBounds(
            min_climb_rate_mps=0.0,
            max_climb_rate_mps=0.0,
            min_turn_rate_degps=0.0,
            max_turn_rate_degps=0.0,
            min_true_airspeed_mps=200.0,
            max_true_airspeed_mps=200.0,
            control_step_count=1,
        ),
        dt_seconds=60.0,
        step_count=1,
        model_version="aircraft-dynamics-1.0.0",
    )
    return evaluate_reachability(request)


def load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as source:
        loaded = json.load(source)
    assert isinstance(loaded, dict)
    return loaded


def snapshot(record) -> dict[str, Any]:
    return {
        "duration_ms": record.duration_ms,
        "failure_kind": record.failure_kind,
        "hypothesis_count": record.hypothesis_count,
        "input_hash": SHA256_PLACEHOLDER,
        "metadata_json": record.metadata_json,
        "normalization_error": record.normalization_error,
        "op_signature_hash": SHA256_PLACEHOLDER,
        "output_hash": SHA256_PLACEHOLDER,
        "pre_normalization_mass": record.pre_normalization_mass,
        "record_count": record.record_count,
        "stage_id": record.stage_id,
        "stage_index": record.stage_index,
        "status": record.status.value,
        "trace_hash": SHA256_PLACEHOLDER,
    }


def test_adapter_preserves_source_hashes_exactly() -> None:
    summary = build_summary()
    record = ReachabilityTraceAdapter.adapt(summary, stage_index=3)

    assert record.input_hash == summary.input_hash
    assert record.output_hash == summary.output_hash
    assert record.op_signature_hash == summary.op_signature_hash
    assert record.trace_hash == compose_step_hash(
        input_hash=summary.input_hash,
        output_hash=summary.output_hash,
        op_signature_hash=summary.op_signature_hash,
    )


def test_adapter_maps_counts_and_leaves_bayesian_fields_unset() -> None:
    summary = build_summary()
    record = ReachabilityTraceAdapter.adapt(summary, stage_index=3)

    assert record.record_count == summary.reachable_state_count
    assert record.hypothesis_count is None
    assert record.normalization_error is None
    assert record.pre_normalization_mass is None


def test_adapter_replay_is_deterministic_and_source_is_unchanged() -> None:
    summary = build_summary()
    before = summary.to_payload()

    first = ReachabilityTraceAdapter.adapt(summary, stage_index=3)
    second = ReachabilityTraceAdapter.adapt(summary, stage_index=3)

    assert first == second
    assert summary.to_payload() == before


def test_duration_does_not_change_identity_hashes() -> None:
    summary = build_summary()
    first = ReachabilityTraceAdapter.adapt(summary, stage_index=3, duration_ms=1.0)
    second = ReachabilityTraceAdapter.adapt(summary, stage_index=3, duration_ms=2.0)

    assert first.input_hash == second.input_hash
    assert first.output_hash == second.output_hash
    assert first.op_signature_hash == second.op_signature_hash
    assert first.trace_hash == second.trace_hash


def test_metadata_is_canonical_and_contains_envelope_fields() -> None:
    summary = build_summary()
    record = ReachabilityTraceAdapter.adapt(summary, stage_index=3)

    assert record.metadata_json is not None
    metadata = json.loads(record.metadata_json)
    assert metadata["contract_version"] == "L1.3"
    assert metadata["state_count"] == summary.reachable_state_count
    assert metadata["control_count"] == 1
    assert "envelope_metadata" in metadata


def test_invalid_stage_index_and_duration_fail_closed() -> None:
    summary = build_summary()

    with pytest.raises(ValueError, match="stage_index"):
        ReachabilityTraceAdapter.adapt(summary, stage_index=-1)
    with pytest.raises(ValueError, match="duration_ms"):
        ReachabilityTraceAdapter.adapt(
            summary,
            stage_index=0,
            duration_ms=math.inf,
        )


def test_reference_trace_snapshot_matches_fixture() -> None:
    record = ReachabilityTraceAdapter.adapt(build_summary(), stage_index=3)

    assert snapshot(record) == load_fixture()
