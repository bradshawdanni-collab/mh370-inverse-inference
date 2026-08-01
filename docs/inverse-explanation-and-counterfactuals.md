# L4.0 Inverse Explanation and Counterfactual Contract

## Purpose

L4.0 explains one deterministic L3 combined admissibility result without adding a new inference layer.

It records:

- every canonical L3 constraint evaluated;
- the ordered failed constraints;
- the fixed assumptions required to interpret the result;
- the minimal governed changes needed to reverse a `NOT_ADMISSIBLE` result;
- exact L0, L1, L2, and L3 provenance identities;
- a canonical SHA-256 explanation hash.

## Counterfactual semantics

Each failed L3 constraint maps to exactly one governed change:

| Failed constraint | Required change |
|---|---|
| `BTO_GEOMETRY_ADMITTED` | `ADMIT_BTO_GEOMETRY` |
| `AIRCRAFT_REACHABILITY_ADMISSIBLE` | `SATISFY_REACHABILITY` |
| `BFO_VALIDATION_ADMITTED` | `ADMIT_BFO_VALIDATION` |
| `BFO_VALIDATION_PASS` | `PASS_BFO_VALIDATION` |

The change set is minimal by construction: it contains one action for each failed constraint and no action for a satisfied constraint. Ordering follows the canonical L3 constraint order.

An `ADMISSIBLE` result has no failed constraints and therefore no reversing change within the bounded L3 contract. L4.0 does not invent a failure condition for an admitted result.

## Determinism

The explanation hash is computed from canonical JSON with sorted keys and compact separators. The hash binds the disposition, assumptions, failed constraints, counterfactual changes, exclusions, and full provenance record.

## Scope boundary

L4.0 does not:

- assign probabilities;
- rank trajectories or hypotheses;
- select endpoints;
- recommend search areas;
- combine debris evidence;
- make a crash-location claim.
