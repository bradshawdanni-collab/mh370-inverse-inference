"""Deterministic GeoJSON serialization for geodetic loci."""

from __future__ import annotations

import json
from collections.abc import Sequence

from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint


def locus_to_geojson(points: Sequence[GeodeticPoint], *, name: str) -> str:
    """Serialize a locus as a stable GeoJSON FeatureCollection."""
    coordinates = [
        [point.longitude_deg, point.latitude_deg] for point in points
    ]
    payload = {
        "features": [
            {
                "geometry": {
                    "coordinates": coordinates,
                    "type": "LineString",
                },
                "properties": {"name": name},
                "type": "Feature",
            }
        ],
        "type": "FeatureCollection",
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
