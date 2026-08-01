# L1.1 Aircraft State Input Contract

## Purpose

L1.1 defines immutable aircraft-state input values and deterministic state-transition descriptions only.

The repository already contains a legacy dynamics `AircraftState` used by existing propagation, reachability, and consistency modules. L1.1 does not replace or silently reinterpret that type. The bounded contract is therefore named `AircraftStateInput` and is isolated in `aircraft/state_contract.py`.

## Contract

`AIRCRAFT_STATE_CONTRACT_VERSION` is fixed at `AIRCRAFT-STATE-1`.

An `AircraftStateInput` contains:

- canonical ISO 8601 UTC `Z` timestamp;
- WGS84 latitude and longitude in degrees;
- altitude in metres;
- groundspeed in metres per second;
- heading in degrees within `[0, 360)`;
- exact source artifact identifier and version;
- contract version.

Mass, fuel, true airspeed, wind correction, thrust, drag, climb, descent, turn performance, and aircraft-performance assumptions are excluded from this contract.

## Radar initialisation

`AircraftStateInput.from_radar_track_point` copies the governed `RadarTrackPoint` fields exactly. It does not infer missing values, convert groundspeed to true airspeed, estimate mass or fuel, apply wind correction, reconstruct a radar path, or select a trajectory.

## Transition semantics

`AircraftStateTransition` records two `AircraftStateInput` values and the exact positive elapsed time between their timestamps. It validates strict timestamp ordering and requires the stored elapsed time to equal the deterministic timestamp difference.

A transition is descriptive only. It does not assert that the movement is physically reachable or compliant with any operating envelope.

## Compatibility boundary

Existing propagation, reachability, factory, trajectory-consistency, and performance-envelope modules continue to consume the pre-existing dynamics `AircraftState`. L1.1 does not modify those scientific behaviours. A later governed adapter may convert an admitted `AircraftStateInput` into a dynamics state only after the required performance, mass, wind, and true-airspeed assumptions are separately admitted.

## Scope boundary

No reachability calculation, propagation, fuel burn, performance envelope, BFO inversion, trajectory inference, ranking, endpoint selection, search-area recommendation, or crash-location claim is introduced by L1.1.
