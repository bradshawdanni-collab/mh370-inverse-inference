"""SATCOM geometry and measurement models."""

from mh370_inverse_inference.satcom.bto import (
    SPEED_OF_LIGHT_M_S,
    timing_error_to_range_m,
)
from mh370_inverse_inference.satcom.export import (
    EXPORT_SCHEMA,
    EXPORT_SCHEMA_VERSION,
    export_uncertainty_bands_csv,
    export_uncertainty_bands_geojson,
)
from mh370_inverse_inference.satcom.locus import (
    SurfaceLocusPoint,
    SurfaceLocusResult,
    generate_surface_locus,
)
from mh370_inverse_inference.satcom.satellite import SatellitePosition
from mh370_inverse_inference.satcom.slant_range import slant_range_m
from mh370_inverse_inference.satcom.uncertainty import (
    BandIdentity,
    SlantRangeBand,
    SlantRangeUncertainty,
    SlantRangeUncertaintyBands,
    generate_uncertainty_bands,
)
from mh370_inverse_inference.satcom.validation import (
    BTO_POINT_MATCHING_CONFIGURATION_ID,
    BTOValidationResult,
    BTOValidationSample,
    PublishedBTOBenchmark,
    PublishedBTOBenchmarkPoint,
    compare_published_bto_benchmark,
    load_published_bto_benchmark_csv,
)
from mh370_inverse_inference.satcom.wgs84 import (
    WGS84_A_M,
    WGS84_B_M,
    WGS84_E2,
    WGS84_EP2,
    WGS84_F,
    ECEFPoint,
    GeodeticPoint,
    ecef_distance_m,
    ecef_to_geodetic,
    geodetic_to_ecef,
    normalize_longitude_deg,
)

__all__ = [
    "BTO_POINT_MATCHING_CONFIGURATION_ID",
    "BTOValidationResult",
    "BTOValidationSample",
    "BandIdentity",
    "ECEFPoint",
    "EXPORT_SCHEMA",
    "EXPORT_SCHEMA_VERSION",
    "GeodeticPoint",
    "PublishedBTOBenchmark",
    "PublishedBTOBenchmarkPoint",
    "SPEED_OF_LIGHT_M_S",
    "SatellitePosition",
    "SlantRangeBand",
    "SlantRangeUncertainty",
    "SlantRangeUncertaintyBands",
    "SurfaceLocusPoint",
    "SurfaceLocusResult",
    "WGS84_A_M",
    "WGS84_B_M",
    "WGS84_E2",
    "WGS84_EP2",
    "WGS84_F",
    "compare_published_bto_benchmark",
    "ecef_distance_m",
    "ecef_to_geodetic",
    "export_uncertainty_bands_csv",
    "export_uncertainty_bands_geojson",
    "generate_surface_locus",
    "generate_uncertainty_bands",
    "geodetic_to_ecef",
    "load_published_bto_benchmark_csv",
    "normalize_longitude_deg",
    "slant_range_m",
    "timing_error_to_range_m",
]
