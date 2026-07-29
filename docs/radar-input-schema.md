# L1.0 Radar Track Input Schema

## Status

This document defines the bounded Issue #83 input contract used to initialize later L1 aircraft-state and reachability work.

The contract version is:

```text
RADAR-INPUT-1
```

## Purpose

The schema records one radar observation with explicit time, position, altitude, groundspeed, heading, provenance identity, and uncertainty values. It validates input shape only. It does not reconstruct a radar track or infer aircraft behaviour.

## Required fields

```yaml
radar_track_point:
  timestamp_utc:
  latitude_deg:
  longitude_deg:
  altitude_m:
  groundspeed_mps:
  heading_deg:
  source_id:
  source_version:
  uncertainty:
    position_m:
    speed_mps:
    heading_deg:
```

## Validation rules

- timestamps must be valid ISO 8601 strings using canonical UTC `Z` notation;
- latitude must be within `[-90, 90]`;
- longitude must be within `[-180, 180]`;
- heading must be within `[0, 360)`;
- groundspeed must be non-negative;
- uncertainty values must be non-negative;
- source identity and version must be non-blank;
- the referenced source must exist in the exact provenance registry snapshot;
- the source state must be `PROPOSED` or `ADMITTED`.

The contract fails closed. Invalid or unresolved values raise errors rather than being normalized, guessed, or silently replaced.

## Provenance boundary

`source_id` and `source_version` resolve through the repository provenance registry established by Issue #9. The radar schema does not create a second source authority and does not perform latest-version or nearest-source fallback.

A `PROPOSED` source may be represented so the repository can explicitly preserve an unadmitted historical input during review. Downstream computations must apply their own admission requirements before using that source in scientific results.

## AircraftState boundary

This stage creates a validated input record suitable for a later `AircraftState` initialization adapter. It does not yet implement that adapter, great-circle propagation, turn-rate envelopes, fuel consumption, or reachability.

Historical-radar-dependent propagation remains blocked until Issue #83 is complete and merged.

## Performance-data caveat

Any Boeing 777-200ER performance model used later in L1 is an approximate envelope unless authoritative aircraft-performance data has been admitted through the repository provenance process. No performance assumption gains authority merely because it appears in code or documentation.

## Explicit exclusions

This schema does not introduce:

- radar reconstruction;
- full aircraft dynamics;
- trajectory inference;
- BFO inversion;
- debris drift;
- Bayesian inference;
- endpoint selection;
- search-area recommendation;
- crash-location claims.
