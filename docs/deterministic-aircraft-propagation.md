# L1.3 Deterministic Aircraft Propagation

## Purpose

L1.3 defines one deterministic kinematic propagation step against an admitted, source-bounded operating envelope.

## Inputs

The propagation contract accepts:

- one governed `AircraftStateInput`;
- one explicit `PropagationCommand`;
- one `AircraftOperatingEnvelope` whose admission state is `ADMITTED`.

The command supplies:

- positive elapsed time;
- target groundspeed;
- target altitude;
- target heading.

## Validation

The propagation step fails closed when:

- the envelope is not admitted;
- target speed is outside the admitted speed bounds;
- target altitude is outside the admitted altitude bounds;
- commanded climb exceeds the admitted climb-rate bound;
- commanded descent exceeds the admitted descent-rate bound;
- commanded turn exceeds the admitted turn-rate bound;
- any numeric value is non-finite or otherwise invalid.

Heading validation uses the shortest angular difference across the 0/360-degree boundary.

## Output

A successful step returns:

- the deterministic next `AircraftStateInput`;
- an `AircraftStateTransition` with exact elapsed time;
- preserved state source identity and version;
- preserved envelope source identity, version, and model version.

Latitude and longitude remain unchanged in L1.3. Position propagation is not introduced by this bounded contract.

## Scope boundary

L1.3 does not:

- estimate fuel burn or aircraft mass;
- apply wind, thrust, drag, or aerodynamic performance models;
- process BFO or SATCOM residuals;
- infer a trajectory or endpoint;
- determine multi-step reachability;
- rank candidates or recommend a search area;
- make a crash-location claim.

Those capabilities require later governed milestones.
