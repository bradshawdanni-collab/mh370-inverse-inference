"""Deterministic CSV serialization for geodetic loci."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from io import StringIO

from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint


def locus_to_csv(points: Sequence[GeodeticPoint]) -> str:
    """Serialize a locus to stable UTF-8 CSV text."""
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["sequence", "latitude_deg", "longitude_deg", "altitude_m"])
    for index, point in enumerate(points):
        writer.writerow(
            [
                index,
                format(point.latitude_deg, ".12f"),
                format(point.longitude_deg, ".12f"),
                format(point.altitude_m, ".3f"),
            ]
        )
    return buffer.getvalue()
