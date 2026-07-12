"""One-way adapter from accepted evidence into L3.1 interpretation input."""

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.interpretation.models import InterpretationRequest


def build_interpretation_request(
    projection: AcceptedEvidenceProjection,
) -> InterpretationRequest:
    """Canonicalize and seal one accepted projection without interpretation."""
    if type(projection) is not AcceptedEvidenceProjection:
        raise TypeError("projection must be AcceptedEvidenceProjection")
    return InterpretationRequest._from_accepted_projection(projection)
