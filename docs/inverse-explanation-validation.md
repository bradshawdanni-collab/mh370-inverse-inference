# L4.1 Inverse Explanation Validation and Deterministic Replay

## Purpose

L4.1 validates the deterministic inverse explanation produced by L4.0. It independently reconstructs the explanation inputs and verifies that the production explanation is reproducible without introducing new inference.

## Inputs

The validator consumes one `CombinedAdmissibilityResult` from the admitted L3 contract.

## Required checks

The validator verifies, in canonical order:

1. production explanation construction;
2. evaluated constraint ordering;
3. failed-constraint ordering;
4. minimal counterfactual mappings;
5. complete L0, L1, L2, and L3 provenance;
6. exact SHA-256 explanation hash reproduction;
7. deterministic replay serialization.

Representative coverage includes both `ADMISSIBLE` and `NOT_ADMISSIBLE` explanations.

## Output

The immutable validation report returns only `PASS` or `FAIL`, ordered failed checks, exact production and independently reproduced hashes, replay hash, provenance, exclusions, and a canonical report hash.

## Scope boundary

This layer does not assign probabilities, rank trajectories or hypotheses, select endpoints, recommend search areas, combine debris evidence, or make a location claim.

The validation artifact remains `PROPOSED` / `PENDING_CI` until CI, DX.2, representative reproduction, provenance verification, hash verification, and deterministic replay pass. Final admission requires a separate governance change.
