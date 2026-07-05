"""Deterministic environmental grid interpolation with fail-closed bounds."""

from dataclasses import dataclass
from math import isfinite

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class EnvironmentalVector:
    """One immutable interpolated environmental vector sample."""

    u: float
    v: float


class EnvironmentalGridAdapter:
    """Immutable bounded spatio-temporal vector grid adapter."""

    def __init__(
        self,
        times: npt.ArrayLike,
        lats: npt.ArrayLike,
        lons: npt.ArrayLike,
        u_grid: npt.ArrayLike,
        v_grid: npt.ArrayLike,
    ) -> None:
        self._times = self._immutable_array(times)
        self._lats = self._immutable_array(lats)
        self._lons = self._immutable_array(lons)
        self._u_grid = self._immutable_array(u_grid)
        self._v_grid = self._immutable_array(v_grid)

        self._validate_axes()
        expected_shape = (len(self._times), len(self._lats), len(self._lons))
        if self._u_grid.shape != expected_shape or self._v_grid.shape != expected_shape:
            raise ValueError(f"grid shape mismatch: expected {expected_shape}")
        if not np.isfinite(self._u_grid).all() or not np.isfinite(self._v_grid).all():
            raise ValueError("grid values must be finite")

    @staticmethod
    def _immutable_array(values: npt.ArrayLike) -> FloatArray:
        array = np.array(values, dtype=np.float64, copy=True)
        array.setflags(write=False)
        return array

    def _validate_axes(self) -> None:
        for name, axis in (
            ("times", self._times),
            ("latitudes", self._lats),
            ("longitudes", self._lons),
        ):
            if axis.ndim != 1:
                raise ValueError(f"{name} must be one-dimensional")
            if len(axis) < 2:
                raise ValueError(f"{name} must contain at least two coordinates")
            if not np.isfinite(axis).all():
                raise ValueError(f"{name} must be finite")
            if not np.all(np.diff(axis) > 0.0):
                raise ValueError(f"{name} must be strictly increasing")

        if self._lats[0] < -90.0 or self._lats[-1] > 90.0:
            raise ValueError("latitude axis must remain within [-90, 90]")
        if self._lons[0] < -180.0 or self._lons[-1] > 180.0:
            raise ValueError("longitude axis must remain within [-180, 180]")

    @staticmethod
    def _cell(axis: FloatArray, coordinate: float) -> tuple[int, float]:
        index = int(np.searchsorted(axis, coordinate, side="right") - 1)
        index = max(0, min(index, len(axis) - 2))
        lower = float(axis[index])
        upper = float(axis[index + 1])
        fraction = (coordinate - lower) / (upper - lower)
        return index, fraction

    def sample_vector(self, *, t: float, lat: float, lon: float) -> EnvironmentalVector:
        """Interpolate one vector without extrapolation or hidden state."""
        if not all(isfinite(value) for value in (t, lat, lon)):
            raise ValueError("query coordinates must be finite")
        if not float(self._times[0]) <= t <= float(self._times[-1]):
            raise ValueError("temporal query is outside dataset bounds")
        if not float(self._lats[0]) <= lat <= float(self._lats[-1]):
            raise ValueError("latitude query is outside dataset bounds")
        if not float(self._lons[0]) <= lon <= float(self._lons[-1]):
            raise ValueError("longitude query is outside dataset bounds")

        time_index, time_fraction = self._cell(self._times, t)
        u0, v0 = self._bilinear(time_index=time_index, lat=lat, lon=lon)
        u1, v1 = self._bilinear(time_index=time_index + 1, lat=lat, lon=lon)

        return EnvironmentalVector(
            u=u0 + time_fraction * (u1 - u0),
            v=v0 + time_fraction * (v1 - v0),
        )

    def _bilinear(self, *, time_index: int, lat: float, lon: float) -> tuple[float, float]:
        lat_index, lat_fraction = self._cell(self._lats, lat)
        lon_index, lon_fraction = self._cell(self._lons, lon)

        def interpolate(grid: FloatArray) -> float:
            lower_left = float(grid[time_index, lat_index, lon_index])
            lower_right = float(grid[time_index, lat_index, lon_index + 1])
            upper_left = float(grid[time_index, lat_index + 1, lon_index])
            upper_right = float(grid[time_index, lat_index + 1, lon_index + 1])
            lower = lower_left + lon_fraction * (lower_right - lower_left)
            upper = upper_left + lon_fraction * (upper_right - upper_left)
            return lower + lat_fraction * (upper - lower)

        return interpolate(self._u_grid), interpolate(self._v_grid)
