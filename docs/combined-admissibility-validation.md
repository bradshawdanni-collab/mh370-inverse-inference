# L3.1 Combined Admissibility Validation and Deterministic Replay

## Purpose

This gate independently reproduces the L3.0 combined BTO, BFO, and aircraft reachability admissibility outcome and verifies deterministic replay.

## Inputs

The validator consumes only already-governed L3.0 inputs:

- admitted L0 BTO provenance linkage;
- deterministic L1 reachability output;
- admitted L2 BFO validation wrapper.

## Validation checks

The validator freezes this ordered check sequence:

1. production evaluation;
2. independent reproduction;
3. disposition match;
4. failed-constraint order match;
5. L0 provenance match;
6. L1 provenance match;
7. L2 provenance match;
8. deterministic replay match.

Representative `ADMISSIBLE` and `NOT_ADMISSIBLE` outcomes are reproduced. The independent path does not call the production combined evaluator to determine its failed constraints.

## Determinism

The production payload is canonically serialized with sorted JSON keys and compact separators, then hashed with SHA-256. The complete validation report is hashed independently using the same canonical encoding.

## Scope boundary

This gate does not:

- assign probabilities;
- rank trajectories or hypotheses;
- select endpoints;
- recommend search areas;
- combine debris evidence;
- make a crash-location claim.

The validation artifact remains `PROPOSED` / `PENDING_CI` until CI, DX.2, representative outcome reproduction, provenance checks, and deterministic replay have passed. Final admission is a separate governance change.
