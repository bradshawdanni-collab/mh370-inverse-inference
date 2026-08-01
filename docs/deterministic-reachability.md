# L1.4 Deterministic Reachability Contract

## Purpose

The L1.4 contract evaluates whether one observed aircraft-state transition is
admissible under an admitted aircraft operating envelope.

It compares two immutable `AircraftStateInput` records and returns one
immutable `ReachabilityResult`.

## Inputs

- governed start state;
- governed end state;
- admitted `AircraftOperatingEnvelope`.

The elapsed time is derived from the canonical UTC timestamps carried by the
two states. The end timestamp must be later than the start timestamp.

## Deterministic checks

The evaluator checks, in fixed order:

1. end speed is inside the admitted speed bounds;
2. end altitude is inside the admitted altitude bounds;
3. climb rate does not exceed the admitted maximum;
4. descent rate does not exceed the admitted maximum;
5. shortest-angle heading change does not exceed the admitted turn-rate limit.

Failures are returned as an ordered tuple of explicit constraint identifiers.
An admissible result has an empty failure tuple. An inadmissible result must
contain at least one failed constraint.

## Provenance

The result preserves:

- start-state source ID and version;
- end-state source ID and version;
- envelope source ID and version;
- envelope model version;
- reachability contract version.

## Scope boundary

This contract does not:

- propagate a trajectory;
- estimate fuel burn;
- apply wind or aerodynamic models;
- process BFO or BTO;
- rank hypotheses;
- infer endpoints or search areas;
- make a crash-location claim.

It provides only a deterministic transition-admissibility result under the
explicit admitted envelope.
