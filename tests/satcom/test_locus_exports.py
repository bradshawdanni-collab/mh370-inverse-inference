"""Tests for canonical SATCOM uncertainty-band CSV and GeoJSON exports."""

import csv
import io
import json

import pytest

from mh370_inverse_inference.satcom.export import (
    EXPORT_SCHEMA,
    EXPORT_SCHEMA_VERSION,
    export_uncertainty_bands_csv,
    export_uncertainty_bands_geojson,
)
from mh370_inverse_inference.satcom.satellite import SatellitePosition
from mh370_inverse_inference.satcom.uncertainty import (
    SlantRangeUncertainty,
    SlantRangeUncertaintyBands,
    generate_uncertainty_bands,
)


def _bands() -> SlantRangeUncertaintyBands:
    satellite = SatellitePosition.from_geodetic(
        epoch_utc="2014-03-08T00:19:29Z",
        latitude_deg=0.0,
        longitude_deg=64.5,
        altitude_m=35_786_000.0,
    )
    uncertainty = SlantRangeUncertainty(
        nominal_range_m=36_000_000.0,
        timing_range_uncertainty_m=10_000.0,
        satellite_position_bias_m=250.0,
    )
    return generate_uncertainty_bands(
        satellite,
        uncertainty,
        tolerance_m=10.0,
        longitude_step_deg=5.0,
        latitude_step_deg=5.0,
        minimum_longitude_deg=40.0,
        maximum_longitude_deg=90.0,
        minimum_latitude_deg=-30.0,
        maximum_latitude_deg=30.0,
    )


def test_csv_export_is_deterministic() -> None:
    bands = _bands()

    assert export_uncertainty_bands_csv(bands) == export_uncertainty_bands_csv(bands)


def test_csv_export_uses_canonical_columns_and_order() -> None:
    text = export_uncertainty_bands_csv(_bands())
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    assert reader.fieldnames == [
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
    ]
    assert text.endswith("\n")
    assert "\r\n" not in text
    assert rows
    assert [row["band"] for row in rows] == sorted(
        (row["band"] for row in rows),
        key=("lower", "nominal", "upper").index,
    )


def test_csv_export_contains_explicit_metadata_and_zero_altitude() -> None:
    rows = list(csv.DictReader(io.StringIO(export_uncertainty_bands_csv(_bands()))))

    assert all(row["schema"] == EXPORT_SCHEMA for row in rows)
    assert all(row["schema_version"] == EXPORT_SCHEMA_VERSION for row in rows)
    assert all(row["altitude_m"] == "0.0" for row in rows)
    assert all(row["timing_range_uncertainty_m"] == "10000.0" for row in rows)
    assert all(row["satellite_position_bias_m"] == "250.0" for row in rows)


def test_geojson_export_is_deterministic_and_canonical() -> None:
    bands = _bands()
    first = export_uncertainty_bands_geojson(bands)
    second = export_uncertainty_bands_geojson(bands)

    assert first == second
    assert first.endswith("\n")
    assert " " not in first
    assert "\n" not in first[:-1]


def test_geojson_export_has_required_schema_and_metadata() -> None:
    payload = json.loads(export_uncertainty_bands_geojson(_bands()))

    assert payload["type"] == "FeatureCollection"
    assert payload["schema"] == EXPORT_SCHEMA
    assert payload["schema_version"] == EXPORT_SCHEMA_VERSION
    assert payload["metadata"] == {
        "band_order": ["lower", "nominal", "upper"],
        "coordinate_order": [
            "longitude_deg",
            "latitude_deg",
            "altitude_m",
        ],
        "nominal_range_m": 36_000_000.0,
        "timing_range_uncertainty_m": 10_000.0,
        "satellite_position_bias_m": 250.0,
        "satellite_epoch_utc": "2014-03-08T00:19:29Z",
    }


def test_geojson_features_preserve_band_and_point_order() -> None:
    payload = json.loads(export_uncertainty_bands_geojson(_bands()))
    features = payload["features"]

    assert features
    identities = [feature["properties"]["band"] for feature in features]
    assert identities == sorted(
        identities,
        key=("lower", "nominal", "upper").index,
    )

    for feature in features:
        coordinates = feature["geometry"]["coordinates"]
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        assert len(coordinates) == 3
        assert coordinates[2] == 0.0
        assert set(feature["properties"]) == {
            "band",
            "point_index",
            "target_range_m",
            "tolerance_m",
        }


def test_exports_reject_wrong_input_type() -> None:
    with pytest.raises(TypeError, match="SlantRangeUncertaintyBands"):
        export_uncertainty_bands_csv(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="SlantRangeUncertaintyBands"):
        export_uncertainty_bands_geojson(object())  # type: ignore[arg-type]


def test_exports_do_not_add_dynamic_identifiers() -> None:
    csv_text = export_uncertainty_bands_csv(_bands())
    geojson_text = export_uncertainty_bands_geojson(_bands())

    for forbidden in ("uuid", "generated_at", "exported_at", "timestamp"):
        assert forbidden not in csv_text.lower()
        assert forbidden not in geojson_text.lower()
