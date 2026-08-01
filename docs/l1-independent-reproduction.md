# L1 Independent Deterministic Reproduction

## Purpose

This gate independently reproduces representative L1.3 propagation and L1.4 reachability outcomes without calling the production propagation or reachability functions.

## Inputs

The reproduction accepts:

- a governed start `AircraftStateInput`;
- a governed expected end `AircraftStateInput`;
- an `ADMITTED` `AircraftOperatingEnvelope`;
- an explicit positive elapsed time.

## Ordered checks

The independent implementation evaluates these checks in fixed order:

1. timestamp reproduction;
2. speed-envelope compliance;
3. altitude-envelope compliance;
4. climb-rate compliance;
5. descent-rate compliance;
6. shortest-angle turn-rate compliance;
7. provenance preservation.

## Recorded outputs

The report records:

- reproduced next-state fields;
- deterministic reachability disposition;
- ordered failed checks;
- climb, descent, and turn residual margins;
- exact start, end, and envelope provenance identities;
- explicit exclusions;
- a canonical SHA-256 report hash;
- overall `PASS` or `FAIL` disposition.

## Independence boundary

The reproduction module does not import or call the production L1.3 `propagate_state` function or the production L1.4 `evaluate_reachability` function.

## Exclusions

This gate does not:

- estimate fuel burn;
- model wind or aerodynamics;
- process BFO or BTO;
- rank trajectories or hypotheses;
- infer endpoints or search areas;
- make a crash-location claim.

## Admission status

The repository validation artifact remains `PROPOSED` and `PENDING_CI` until all CI and DX.2 checks pass. A final admission update and Issue #5 closure require a separate explicit completion step.
