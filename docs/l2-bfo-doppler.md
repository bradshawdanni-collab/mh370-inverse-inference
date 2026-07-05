# L2 BFO Doppler Inversion and Vector Calculation

## Purpose

L2 converts explicit Earth-centred, Earth-fixed positions and velocities into signed line-of-sight range rates, classical Doppler contributions, predicted Burst Frequency Offset values, and invertible scalar radial-velocity constraints.

The layer is deterministic. It does not estimate a full aircraft velocity vector from one BFO observation and does not embed historical calibration constants.

## Coordinate frame

All positions use metres in the Earth-centred, Earth-fixed frame. All velocities use metres per second in the same frame.

A line-of-sight unit vector points from transmitter to receiver:

```text
u = (r_receiver - r_transmitter) / |r_receiver - r_transmitter|
```

The signed range rate is:

```text
range_rate = (v_receiver - v_transmitter) dot u
```

Interpretation:

- positive range rate: increasing separation;
- negative range rate: closing motion;
- zero range rate: no relative radial motion.

## Classical Doppler approximation

For carrier frequency `f` and signed range rate `r_dot`:

```text
delta_f = -(f / c) * r_dot
```

where `c = 299792458 m/s`.

Under this convention:

- separating motion produces a negative shift;
- closing motion produces a positive shift.

This is the non-relativistic, first-order Doppler approximation. The code rejects non-positive carrier frequencies and undefined line-of-sight geometry.

## Two-leg composition

The implemented forward model separates the ground-to-satellite and satellite-to-aircraft legs:

```text
predicted_bfo = uplink_doppler + downlink_doppler + bias
```

The equipment or calibration bias is supplied by the caller. It is never hard-coded in L2.

The returned `DopplerComponents` object preserves all three terms for audit and replay.

## Inversion

After removing the known uplink and supplied bias terms:

```text
downlink_doppler = observed_bfo - uplink_doppler - bias
```

The required satellite-aircraft range rate is:

```text
range_rate = -(c / f_downlink) * downlink_doppler
```

The aircraft velocity component along the satellite-to-aircraft line of sight is then:

```text
v_aircraft_los = range_rate + v_satellite_los
```

This result is one scalar projection. It is not a complete heading, ground-speed, or true-airspeed solution.

## Failure discipline

L2 fails closed when:

- a position pair is coincident;
- a carrier frequency is zero, negative, or non-finite;
- velocity or BFO inputs are non-finite;
- a requested inversion lacks the explicit external terms required by the equation.

## Verification

The tests prove:

- line-of-sight direction;
- zero-motion neutrality;
- closing/separating sign behavior;
- forward/inverse round-trip recovery;
- separate inspection of uplink, downlink, and bias terms;
- residual convention of observed minus predicted.
