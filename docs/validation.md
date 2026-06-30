# Validation

Validation occurs module by module before joint inference.

## L0 acceptance criteria

- Reproduce published BTO-derived arc geometry within the documented uncertainty envelope.
- Keep timing uncertainty separate from satellite ephemeris bias.
- Use geodetic calculations rather than planar map distances.
- Pass deterministic unit tests for timing-to-range conversion.
- Record all source files, transformations, and assumptions.

## Later validation targets

- BFO: reproduce benchmark Doppler calculations.
- Aircraft: remain inside validated Boeing 777 performance envelopes.
- Transport: reproduce drifter trajectories within uncertainty.
- Search: reproduce published coverage and detection assumptions.
- Debris: recover observed landfall distributions in ensemble tests.

A posterior map is not accepted unless sensitivity and ablation analyses accompany it.
