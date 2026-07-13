"""Canonical deterministic exports for SATCOM uncertainty-band loci."""

from __future__ import annotations

import csv
import io
import json

from mh370_inverse_inference.satcom.uncertainty import (
    SlantRangeUncertaintyBands,
)

EXPORT_SCHEMA = "mh370-inverse-inference.satcom.uncertainty-bands"
EXPORT_SCHEMA_VERSION = "1.0.0"

_CSV_COLUMNS = (
    "schema",
    "schema_version",
    "band",
    "point_index",
    "longitude_deg",
    "latitude_deg",
    "altitude_m",
    "target_range_m",
    "tolerance_m",
    "timing_range_uncertainty_m",
    "satellite_position_bias_m",
)


def _require_bands(value: SlantRangeUncertaintyBands) -> None:
    if type(value) is not SlantRangeUncertaintyBands:
        raise TypeError("bands must be SlantRangeUncertaintyBands")


def _format_float(value: float) -> str:
    """Return one stable decimal representation without exponent notation."""
    text = format(float(value), ".12f").rstrip("0").rstrip(".")
    return text if "." in text else f"{text}.0"


def export_uncertainty_bands_csv(bands: SlantRangeUncertaintyBands) -> str:
    """Serialize uncertainty-band points as canonical UTF-8 CSV text."""
    _require_bands(bands)

    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=_CSV_COLUMNS,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()

    for band in bands.bands:
        for point_index, point in enumerate(band.locus.points):
            writer.writerow(
                {
                    "schema": EXPORT_SCHEMA,
                    "schema_version": EXPORT_SCHEMA_VERSION,
                    "band": band.identity,
                    "point_index": str(point_index),
                    "longitude_deg": _format_float(point.geodetic.longitude_deg),
                    "latitude_deg": _format_float(point.geodetic.latitude_deg),
                    "altitude_m": _format_float(point.geodetic.altitude_m),
                    "target_range_m": _format_float(band.target_range_m),
                    "tolerance_m": _format_float(band.locus.tolerance_m),
                    "timing_range_uncertainty_m": _format_float(
                        bands.uncertainty.timing_range_uncertainty_m
                    ),
                    "satellite_position_bias_m": _format_float(
                        bands.uncertainty.satellite_position_bias_m
                    ),
                }
            )

    return output.getvalue()


def export_uncertainty_bands_geojson(
    bands: SlantRangeUncertaintyBands,
) -> str:
    """Serialize uncertainty-band points as canonical GeoJSON text."""
    _require_bands(bands)

    features: list[dict[str, object]] = []
    for band in bands.bands:
        for point_index, point in enumerate(band.locus.points):
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(point.geodetic.longitude_deg),
                            float(point.geodetic.latitude_deg),
                            0.0,
                        ],
                    },
                    "properties": {
                        "band": band.identity,
                        "point_index": point_index,
                        "target_range_m": float(band.target_range_m),
                        "tolerance_m": float(band.locus.tolerance_m),
                    },
                }
            )

    payload = {
        "type": "FeatureCollection",
        "schema": EXPORT_SCHEMA,
        "schema_version": EXPORT_SCHEMA_VERSION,
        "metadata": {
            "band_order": ["lower", "nominal", "upper"],
            "coordinate_order": [
                "longitude_deg",
                "latitude_deg",
                "altitude_m",
            ],
            "nominal_range_m": float(bands.uncertainty.nominal_range_m),
            "timing_range_uncertainty_m": float(
                bands.uncertainty.timing_range_uncertainty_m
            ),
            "satellite_position_bias_m": float(
                bands.uncertainty.satellite_position_bias_m
            ),
            "satellite_epoch_utc": bands.bands[0].locus.satellite.epoch_utc,
        },
        "features": features,
    }
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
