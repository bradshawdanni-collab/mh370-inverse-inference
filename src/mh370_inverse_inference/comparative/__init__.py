"""Deterministic comparative assessment contracts."""

from mh370_inverse_inference.comparative.record import (
    ComparativeAssessmentRecord,
    ComparativeAssessmentRelation,
    build_comparative_assessment_record,
)
from mh370_inverse_inference.comparative.request import (
    ComparativeAssessmentRequest,
    build_comparative_assessment_request,
)

__all__ = [
    "ComparativeAssessmentRecord",
    "ComparativeAssessmentRelation",
    "ComparativeAssessmentRequest",
    "build_comparative_assessment_record",
    "build_comparative_assessment_request",
]
