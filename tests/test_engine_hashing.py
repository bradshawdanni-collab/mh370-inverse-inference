"""Tests for canonical engine trace hashing utilities."""

import math

import pytest

from mh370_inverse_inference.engine.hashing import (
    canonical_json_bytes,
    compose_replay_hash,
    compose_step_hash,
    sha256_payload,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def test_mapping_order_does_not_change_canonical_bytes_or_hash() -> None:
    first = {"beta": 2, "alpha": {"y": 2, "x": 1}}
    second = {"alpha": {"x": 1, "y": 2}, "beta": 2}

    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert sha256_payload(first) == sha256_payload(second)


def test_canonical_json_is_utf8_compact_and_preserves_unicode() -> None:
    payload = {"label": "café", "values": [1, 2, 3]}

    assert canonical_json_bytes(payload) == (
        '{"label":"café","values":[1,2,3]}'.encode()
    )


def test_list_order_remains_significant() -> None:
    assert sha256_payload(["H-1", "H-2"]) != sha256_payload(["H-2", "H-1"])


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_float_is_rejected_recursively(value: float) -> None:
    with pytest.raises(ValueError, match="non-finite float"):
        canonical_json_bytes({"outer": [{"value": value}]})


def test_non_string_mapping_keys_are_rejected() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        canonical_json_bytes({1: "invalid"})


def test_unsupported_values_are_rejected() -> None:
    with pytest.raises(TypeError, match="unsupported canonical JSON value"):
        canonical_json_bytes({"value": {1, 2, 3}})


def test_step_hash_is_deterministic_and_field_sensitive() -> None:
    first = compose_step_hash(
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
    )
    second = compose_step_hash(
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
    )
    changed = compose_step_hash(
        input_hash=HASH_A,
        output_hash=HASH_D,
        op_signature_hash=HASH_C,
    )

    assert first == second
    assert first != changed
    assert len(first) == 64


def test_replay_hash_preserves_step_order() -> None:
    first = compose_replay_hash(
        step_hashes=(HASH_A, HASH_B, HASH_C),
        final_posterior_hash=HASH_D,
    )
    reordered = compose_replay_hash(
        step_hashes=(HASH_B, HASH_A, HASH_C),
        final_posterior_hash=HASH_D,
    )

    assert first != reordered


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "input_hash": "bad",
                "output_hash": HASH_B,
                "op_signature_hash": HASH_C,
            },
            "input_hash",
        ),
        (
            {
                "input_hash": HASH_A,
                "output_hash": "B" * 64,
                "op_signature_hash": HASH_C,
            },
            "output_hash",
        ),
    ],
)
def test_step_hash_rejects_malformed_digests(
    kwargs: dict[str, str],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        compose_step_hash(**kwargs)


def test_replay_hash_rejects_empty_or_malformed_inputs() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        compose_replay_hash(step_hashes=(), final_posterior_hash=HASH_D)

    with pytest.raises(ValueError, match=r"step_hashes\[1\]"):
        compose_replay_hash(
            step_hashes=(HASH_A, "bad"),
            final_posterior_hash=HASH_D,
        )
