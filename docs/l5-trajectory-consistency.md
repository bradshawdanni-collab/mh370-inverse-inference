# L5 Trajectory Assembly and Time-Series Consistency

## Purpose

L5 assembles timestamped aircraft states into ordered trajectory segments and evaluates each segment against explicit physical limits.

The layer is deterministic. It does not optimize a path, assign probabilities, smooth measurements, or choose limits automatically.

## Inputs

Each `TrajectoryPoint` contains:

- a finite timestamp in seconds;
- an immutable `AircraftState` from L1;
- an optional candidate-admissibility result from L4.

`TrajectoryLimits` contains explicit maximum values for:

- implied ground speed;
- absolute climb or descent rate;
- absolute turn rate;
- permitted mass increase;
- optional enforcement of L4 endpoint admissibility.

## Segment derivation

For each consecutive pair of points, L5 computes:

```text
duration = t_2 - t_1
surface_distance = spherical great-circle distance
implied_ground_speed = surface_distance / duration
climb_rate = (altitude_2 - altitude_1) / duration
turn_rate = shortest_signed_heading_change / duration
mass_change = mass_2 - mass_1
```

Timestamps must be strictly increasing.

The heading calculation uses the shortest signed angular difference, so a transition from 359 degrees to 1 degree is treated as a 2-degree turn rather than a 358-degree turn.

## Decisions

Each `SegmentDecision` preserves the derived metrics and independent pass/fail flags for speed, climb, turn, mass, and optional endpoint admissibility.

A trajectory is consistent only when every segment is consistent.

## Interpretation boundary

The distance-derived speed is an implied average ground speed over the interval. It is not treated as true airspeed and is not substituted for the L1 `speed_tas` field.

## Failure discipline

L5 fails closed when:

- a timestamp is non-finite;
- timestamps are not strictly increasing;
- fewer than two points are supplied;
- a configured limit is negative or non-finite;
- endpoint admissibility is required and either endpoint is not explicitly admissible.

## Scope boundaries

L5 does not perform route search, dynamic programming, Bayesian inference, interpolation, optimization, or automatic tolerance selection. Those functions belong to later milestones after trajectory consistency is stable.
