# L3.0 Combined BTO + BFO + Reachability Admissibility

## Purpose

This contract combines three already-governed outputs:

1. admitted L0 BTO geometry provenance linkage;
2. deterministic L1 aircraft reachability;
3. admitted L2 BFO validation.

It returns only one deterministic disposition:

- `ADMISSIBLE`; or
- `NOT_ADMISSIBLE`.

## Ordered constraints

Constraints are evaluated and reported in this fixed order:

1. `BTO_GEOMETRY_ADMITTED`
2. `AIRCRAFT_REACHABILITY_ADMISSIBLE`
3. `BFO_VALIDATION_ADMITTED`
4. `BFO_VALIDATION_PASS`

A failed result preserves this order regardless of the order in which callers provide data.

## Provenance

The result records:

- L0 validation identity and output artifact identity;
- L1 reachability contract, state-source and envelope-source identities;
- L2 admission artifact identity, report hash and component-model version;
- the L3 contract version.

## Fail-closed behaviour

The contract rejects incorrect input types. A source that has not already passed its upstream admission boundary cannot produce an `ADMISSIBLE` result.

## Explicit exclusions

This layer does not:

- assign probabilities;
- rank paths or hypotheses;
- select endpoints;
- recommend a search area;
- combine debris or other evidence;
- make a crash-location claim.
