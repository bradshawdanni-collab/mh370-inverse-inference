# L2.2 BFO Model Validation and Independent Reproduction

## Purpose

This milestone validates the admitted L2.1 deterministic BFO component model against an independently calculated component breakdown.

## Contract boundary

The validation gate consumes:

- an admitted `BFOObservation`;
- admitted `BFOComponentInputs`;
- the production L2.1 component model;
- an independent reproduction path that does not call the production component evaluator.

## Deterministic checks

The ordered validation sequence is:

1. observation admitted;
2. component inputs admitted;
3. production component model executed;
4. independent component reproduction executed;
5. component outputs compared;
6. residuals compared;
7. provenance identities preserved.

The report records:

- production and independent component breakdowns;
- maximum component difference in hertz;
- production and independent residuals;
- residual difference in hertz;
- observation, calibration, constants, and model identities;
- explicit scope exclusions;
- a canonical SHA-256 report hash;
- a PASS or FAIL disposition.

## Independent reproduction

The independent path directly reconstructs the canonical component sequence from the governed input record. It does not call `evaluate_bfo_components`.

The production and independent outputs must match exactly for this bounded deterministic contract. Any non-zero component or residual difference produces a FAIL disposition.

## Fail-closed behaviour

Validation rejects:

- non-`BFOObservation` inputs;
- non-`BFOComponentInputs` inputs;
- observations that are not `ADMITTED`;
- component inputs that are not `ADMITTED`.

## Exclusions

This milestone does not:

- invert BFO into a trajectory;
- choose aircraft velocity;
- rank candidate trajectories or hypotheses;
- combine BFO with debris or search evidence;
- infer endpoints;
- select a search area;
- make a crash-location claim.

## Admission posture

`data/satcom/bfo_validation_report_v1.json` remains `PROPOSED` with `PENDING_CI` disposition until CI, DX.2, and the independent-reproduction tests complete successfully. Final admission must occur in a separate governance change.
