# BTO Slant-Range Locus

## Scope

This module converts a satellite ECEF position and a target slant range into candidate WGS84 Earth-surface points. It generates nominal, lower, and upper loci while keeping range uncertainty separate from satellite-position bias.

It does not perform BFO inversion, aircraft dynamics, debris transport, Bayesian inference, or crash-location estimation.

## Method

For a surface point `p` and satellite position `s`, the residual is

\[
f(p)=\lVert p-s\rVert_2-r
\]

where `r` is the target slant range.

For each sampled longitude, the implementation scans latitude for sign changes in `f` and solves each bracket with deterministic bisection. Surface points are represented with WGS84 geodetic coordinates and converted to ECEF before range evaluation.

## Uncertainty

The current interface accepts a symmetric slant-range uncertainty:

\[
r_{lower}=r-\epsilon_r,\qquad r_{upper}=r+\epsilon_r
\]

Satellite ephemeris bias is not folded into `epsilon_r`. It must be represented by perturbing the satellite ECEF position independently.

## Exports

Loci can be serialized deterministically as:

- GeoJSON `LineString` features
- CSV rows containing sequence, latitude, longitude, and altitude

## Validation

Current tests use synthetic, independently constructed surface points to verify:

- residual consistency,
- latitude-root recovery,
- deterministic locus generation,
- deterministic GeoJSON and CSV serialization.

Published ATSB/Inmarsat benchmark validation remains required before Issue #4 can close.

## Limitations

- Longitude and latitude scanning resolution affects point density and root discovery.
- The generated point sequence is not yet topologically sorted into complete closed branches.
- No official MH370 ephemeris or BTO benchmark file has yet been admitted into the source registry.
- Validation plots are not yet implemented.
