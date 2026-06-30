# L0 SATCOM Geometry

## Scope

This module provides deterministic WGS84 geometry primitives for later BTO arc reconstruction. It does not estimate an aircraft trajectory or crash location.

## Mathematical definitions

### Geodetic to ECEF

A WGS84 geodetic point \((\varphi, \lambda, h)\) is converted to Earth-centred, Earth-fixed coordinates using the standard ellipsoidal prime-vertical radius:

\[
N(\varphi)=\frac{a}{\sqrt{1-e^2\sin^2\varphi}}
\]

\[
x=(N+h)\cos\varphi\cos\lambda
\]

\[
y=(N+h)\cos\varphi\sin\lambda
\]

\[
z=(N(1-e^2)+h)\sin\varphi
\]

### Slant range

For two ECEF points \(p_1\) and \(p_2\), slant range is:

\[
r=\lVert p_2-p_1\rVert_2
\]

### Surface distance

Surface distances and forward projections use WGS84 ellipsoidal geodesics through `pyproj.Geod`.

## Assumptions

- WGS84 is the governing Earth reference ellipsoid.
- Satellite and aircraft positions are represented in ECEF for slant-range calculations.
- Timing uncertainty and satellite ephemeris bias remain separate parameters.
- A geodesic circle is a utility object, not yet a complete BTO measurement inversion.

## Validation approach

- Round-trip geodetic/ECEF conversion tests.
- Known Cartesian slant-range tests.
- Known WGS84 equatorial distance tests.
- Closed geodesic-circle and uncertainty-band tests.
- Existing BTO timing-to-range tests remain active.

## Known limitations

- Published MH370 ephemeris and BTO rows are not yet imported.
- The current arc utility generates constant surface-distance circles; exact BTO locus generation from satellite slant range remains the next implementation step.
- No BFO, aircraft dynamics, debris transport, search, or Bayesian inference is included.
