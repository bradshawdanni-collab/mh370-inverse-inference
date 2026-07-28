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
from mh370_inverse_inference.satcom.published_bto import (
    generate_published_bto_zero_height_locus,
    published_bto_aircraft_range_m,
)
from mh370_inverse_inference.satcom.satellite import (
    ECEFVelocity,
    SatellitePosition,
    SatelliteState,
    interpolate_satellite_state_cubic_hermite,
)
from mh370_inverse_inference.satcom.slant_range import slant_range_m
from mh370_inverse_inference.satcom.uncertainty import (
    BandIdentity,
    SlantRangeBand,
    SlantRangeUncertainty,
    SlantRangeUncertaintyBands,
    generate_uncertainty_bands,
)
from mh370_inverse_inference.satcom.validation import (
    ADMITTED_SEVENTH_ARC_BENCHMARK_ID,
    ADMITTED_SEVENTH_ARC_FIXTURE_SHA256,
    BTO_POINT_MATCHING_CONFIGURATION_ID,
    BTOValidationResult,
    BTOValidationSample,
    PublishedBTOBenchmark,
    PublishedBTOBenchmarkPoint,
    compare_published_bto_benchmark,
    load_admitted_seventh_arc_benchmark,
    load_published_bto_benchmark_csv,
    serialize_bto_validation_result_json,
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
    "ADMITTED_SEVENTH_ARC_BENCHMARK_ID",
    "ADMITTED_SEVENTH_ARC_FIXTURE_SHA256",
    "BTO_POINT_MATCHING_CONFIGURATION_ID",
    "BTOValidationResult",
    "BTOValidationSample",
    "BandIdentity",
    "ECEFPoint",
    "ECEFVelocity",
    "EXPORT_SCHEMA",
    "EXPORT_SCHEMA_VERSION",
    "GeodeticPoint",
    "PublishedBTOBenchmark",
    "PublishedBTOBenchmarkPoint",
    "SPEED_OF_LIGHT_M_S",
    "SatellitePosition",
    "SatelliteState",
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
    "generate_published_bto_zero_height_locus",
    "generate_surface_locus",
    "generate_uncertainty_bands",
    "geodetic_to_ecef",
    "interpolate_satellite_state_cubic_hermite",
    "load_admitted_seventh_arc_benchmark",
    "load_published_bto_benchmark_csv",
    "normalize_longitude_deg",
    "published_bto_aircraft_range_m",
    "serialize_bto_validation_result_json",
    "slant_range_m",
    "timing_error_to_range_m",
]
