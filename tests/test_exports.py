import json

from mh370_inverse_inference.io.csv import locus_to_csv
from mh370_inverse_inference.io.geojson import locus_to_geojson
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint


def test_geojson_export() -> None:
    points = (
        GeodeticPoint(-30.0, 90.0),
        GeodeticPoint(-31.0, 91.0),
    )
    output = locus_to_geojson(points, name="nominal")
    payload = json.loads(output)
    assert payload["type"] == "FeatureCollection"
    assert output == locus_to_geojson(points, name="nominal")


def test_csv_export() -> None:
    points = (
        GeodeticPoint(-30.0, 90.0),
        GeodeticPoint(-31.0, 91.0, 100.0),
    )
    output = locus_to_csv(points)
    assert output.startswith("sequence,latitude_deg,longitude_deg,altitude_m\n")
    assert output == locus_to_csv(points)
