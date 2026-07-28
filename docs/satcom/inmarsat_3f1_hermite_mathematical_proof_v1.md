# Inmarsat-3 F1 Cubic-Hermite Mathematical Proof v1

## Status and scope

Artifact ID: `inmarsat-3f1-hermite-mathematical-proof-v1`

Issue: `#172`

Status: `PROPOSED_PENDING_INDEPENDENT_REVIEW`

This document proves the boundary conditions and target-epoch evaluation of the cubic-Hermite interpolation used to derive the Inmarsat-3 F1 ECEF satellite state at `2014-03-08T00:19:29.416Z`.

It is a mathematical verification artifact only. It does not promote evidence admission, create Earth-surface benchmark coordinates, create `benchmark_fixture.csv`, or establish a crash location.

## Frozen provenance references

The proof is evaluated against the frozen records already merged into `main` by PR #176.

| Layer | Artifact ID | SHA-256 |
| --- | --- | --- |
| Published source PDF | `inmarsat-search-for-mh370-2014` | `2ff0f10c1cf0bad299e5398ad9019a113963f6a5bd86b96bf4d04d330bc08028` |
| Extracted Table 4 endpoints | `inmarsat-3f1-table4-endpoints-20140308` | `835c5a93ca9af0c618bb692404a8af59a079aa08af3188df0abcaa3b515eebbc` |
| Hermite transform specification | `inmarsat-3f1-hermite-transform-v1` | `ea135509fc6d1dcc9e2f5dad07780ad74e976337a02ba073351f243c1b79ee82` |
| Derived target state | `inmarsat-3f1-table4-target-state-20140308T001929416Z` | `c61f400c8b27b07b3acc57701d958068ee8cbb2654a5e325e3f2d0f0cb166452` |

The endpoint values are published rounded values. The target state is therefore an interpolation-derived state, not an exact published ephemeris row.

## Inputs

The interpolation interval is

$$
T = 600\ \mathrm{s}.
$$

The target offset from `00:10:00Z` is

$$
t_* = 569.416\ \mathrm{s},
\qquad
u_* = \frac{t_*}{T}
     = 0.949026666666666666\ldots
$$

The frozen Table 4 endpoint state vectors, converted to repository SI units, are

$$
\mathbf r_0 =
\begin{bmatrix}
18177500.0\\
38051700.0\\
440000.0
\end{bmatrix}\mathrm{m},
\qquad
\mathbf v_0 =
\begin{bmatrix}
1.60\\
-1.51\\
-81.88
\end{bmatrix}\mathrm{m\,s^{-1}},
$$

and

$$
\mathbf r_1 =
\begin{bmatrix}
18178400.0\\
38050800.0\\
390500.0
\end{bmatrix}\mathrm{m},
\qquad
\mathbf v_1 =
\begin{bmatrix}
1.50\\
-1.58\\
-83.21
\end{bmatrix}\mathrm{m\,s^{-1}}.
$$

## Cubic-Hermite definition

For normalized parameter

$$
u = \frac{t}{T},
$$

the component-wise cubic-Hermite interpolant is

$$
H(u)
= h_{00}(u)r_0
+ h_{10}(u)T v_0
+ h_{01}(u)r_1
+ h_{11}(u)T v_1,
$$

where

$$
\begin{aligned}
h_{00}(u) &= 2u^3-3u^2+1,\\
h_{10}(u) &= u^3-2u^2+u,\\
h_{01}(u) &= -2u^3+3u^2,\\
h_{11}(u) &= u^3-u^2.
\end{aligned}
$$

Because `u=t/T`, differentiation with respect to physical time gives

$$
H'(t)
= \frac{1}{T}
\left(
h'_{00}(u)r_0
+ h'_{10}(u)T v_0
+ h'_{01}(u)r_1
+ h'_{11}(u)T v_1
\right),
$$

with

$$
\begin{aligned}
h'_{00}(u) &= 6u^2-6u,\\
h'_{10}(u) &= 3u^2-4u+1,\\
h'_{01}(u) &= -6u^2+6u,\\
h'_{11}(u) &= 3u^2-2u.
\end{aligned}
$$

The equations apply independently to the ECEF `x`, `y`, and `z` components.

## Boundary-condition proof

At `u=0`,

$$
(h_{00},h_{10},h_{01},h_{11})=(1,0,0,0),
$$

so

$$
H(0)=r_0.
$$

Also,

$$
(h'_{00},h'_{10},h'_{01},h'_{11})=(0,1,0,0),
$$

therefore

$$
H'(0)=v_0.
$$

At `u=1`,

$$
(h_{00},h_{10},h_{01},h_{11})=(0,0,1,0),
$$

so

$$
H(T)=r_1.
$$

Also,

$$
(h'_{00},h'_{10},h'_{01},h'_{11})=(0,0,0,1),
$$

therefore

$$
H'(T)=v_1.
$$

Thus the interpolation satisfies all four declared boundary constraints exactly:

$$
H(0)=r_0,\qquad H(T)=r_1,
$$

$$
H'(0)=v_0,\qquad H'(T)=v_1.
$$

## Target-epoch evaluation

At `u=u_*`, the basis values are

$$
\begin{aligned}
h_{00} &= 0.007529956075771259259\ldots,\\
h_{10} &= 0.002465837682330074074\ldots,\\
h_{01} &= 0.992470043924228740741\ldots,\\
h_{11} &= -0.045909214939892148148\ldots.
\end{aligned}
$$

The derivative-basis values are

$$
\begin{aligned}
h'_{00} &= -0.290250315733333333333\ldots,\\
h'_{10} &= -0.094151824533333333333\ldots,\\
h'_{01} &= 0.290250315733333333333\ldots,\\
h'_{11} &= 0.803901508800000000000\ldots.
\end{aligned}
$$

High-precision decimal evaluation gives

$$
\mathbf r_* =
\begin{bmatrix}
18178354.2719502609398044\ldots\\
38050848.0648472910208427\ldots\\
393043.6546171822208427\ldots
\end{bmatrix}\mathrm{m},
$$

and

$$
\mathbf v_* =
\begin{bmatrix}
1.4905848175466666667\ldots\\
-1.5633706024586666667\ldots\\
-83.1291442024586666667\ldots
\end{bmatrix}\mathrm{m\,s^{-1}}.
$$

The frozen target-state record stores

$$
\mathbf r_{frozen} =
\begin{bmatrix}
18178354.27195026\\
38050848.06484729\\
393043.6546171822
\end{bmatrix}\mathrm{m},
$$

and

$$
\mathbf v_{frozen} =
\begin{bmatrix}
1.4905848175466667\\
-1.5633706024564664\\
-83.12914420245867
\end{bmatrix}\mathrm{m\,s^{-1}}.
$$

The frozen values agree with the high-precision mathematical evaluation to the repository's independent audit tolerances. The largest absolute position difference is approximately `1.03e-9 m`; the largest absolute velocity difference is approximately `2.21e-12 m/s`.

The small velocity difference is numerical round-off from evaluating the analytic derivative with finite-precision arithmetic and cancellation between large ECEF position terms. It is not a physical correction and does not alter the interpolation contract.

## Deterministic implementation relationship

The repository implementation

`mh370_inverse_inference.satcom.satellite.interpolate_satellite_state_cubic_hermite`

uses the same basis functions and analytic derivative shown above. PR #176 also added an independent scalar implementation and a high-precision Decimal audit that do not call the production interpolation function.

Therefore the frozen target state is reproduced within the declared numerical audit bounds by:

1. the production cubic-Hermite implementation;
2. an independent binary64 implementation; and
3. a high-precision Decimal evaluation of the same mathematical contract.

## Authority boundary

This proof establishes only that the declared deterministic cubic-Hermite transformation:

- satisfies the four endpoint position/velocity boundary constraints;
- evaluates consistently at the selected `569.416 s` target offset; and
- reproduces the frozen target-state representation within the declared numerical audit tolerances.

It does not establish that the rounded Table 4 endpoints are exact operational ephemeris values, does not claim that Hermite interpolation is uniquely physically optimal between those nodes, and does not promote the source or derived state beyond `PROPOSED_PENDING_INDEPENDENT_REVIEW`.

Historical TLE/SGP4 propagation remains secondary corroboration only.

## Next review gate

Independent review should verify:

- the frozen endpoint transcription against the registered source bytes;
- the algebra and derivative convention in this proof;
- the target offset `569.416 s`;
- the stated numerical residual bounds; and
- consistency between this proof, the frozen transformation specification, and the frozen target-state record.

Only after that review should #172 advance to the remaining Perth GES, altitude-convention, WGS84 transformation, transformed-coordinate review, fixture-freeze, and final admission gates.
