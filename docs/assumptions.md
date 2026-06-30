# Assumptions

All assumptions must be explicit, versioned, and testable.

## Initial L0 assumptions

- Earth geometry is represented with WGS84.
- BTO observations define slant-range constraints and map to Earth-surface bands.
- Routine BTO uncertainty is represented separately from systematic satellite-position bias.
- The 00:19 UTC log-on is a special event class and is not treated as an ordinary smooth continuation point.
- No crash-location claim is permitted from BTO geometry alone.

## Deferred assumptions

Aircraft dynamics, debris transport, search detection, biology, atmospheric signals, and hydroacoustics are outside L0 and must enter through separate modules.
