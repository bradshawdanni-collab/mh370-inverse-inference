# References and Evidence Attribution

## Status

This document defines the bounded **Issue #9C** distinction between evidence that
was retrieved into a governed context, evidence that was cited in an output, and
evidence that actually affected a computation or judgement.

It does not admit new scientific sources. Candidate references named in Issue #9
remain candidates until independently verified and admitted through the existing
scientific source-governance process.

## Contract

The repository-level attribution contract is:

```text
PROVENANCE-ATTRIBUTION-1
```

The implementation is in:

```text
src/mh370_inverse_inference/provenance/attribution.py
```

## Three explicit roles

Attribution is represented by three different immutable record types.

### Retrieved evidence

`RetrievedEvidenceRecord` states that one exact `ArtifactReference` was available
to a named review, research, or processing context.

A retrieval record does not state that the artifact was cited, accepted, admitted,
or used in a calculation.

### Cited evidence

`CitationRecord` states that one exact `ArtifactReference` was cited in a named
output context and records a stable locator for the citation.

Citation does not imply scientific admission or computational use. A candidate,
rejected, or otherwise non-admitted artifact may still be cited when discussing
its existence, limitations, or rejection, provided the exact registered artifact
reference is recorded.

### Evidence used by an outcome

`EvidenceUseRecord` states that one exact artifact affected a named computation or
judgement. Its `use_kind` is one of:

```text
COMPUTATION
JUDGEMENT
```

Evidence-use linkage is fail-closed: the referenced artifact must exist exactly in
the provenance registry snapshot and must carry the `ADMITTED` state. A citation
alone can never satisfy this condition.

## Exact-version linkage

Every retrieval, citation, and use record points to an exact `ArtifactReference`:

- stable artifact ID;
- explicit version;
- exact SHA-256 digest.

No lookup falls back to another version or accepts a matching artifact ID with a
different digest.

## Attribution snapshot

`AttributionSnapshot` binds the three record classes to one exact
`ProvenanceRegistrySnapshot` through its `provenance_snapshot_sha256`.

The builder:

- requires all referenced artifacts to exist exactly in that provenance snapshot;
- requires `ADMITTED` state for every evidence-use record;
- preserves retrieval, citation, and use as separate record collections;
- canonicalizes each collection by its stable record ID;
- rejects duplicate IDs across all three record classes;
- hashes the canonical payload deterministically.

The result is an immutable, hash-addressable statement of what was available,
what was cited, and what actually influenced an outcome.

## No implicit promotion

The attribution layer does not:

- promote a retrieved artifact to `VERIFIED` or `ADMITTED`;
- treat a citation as evidence use;
- treat evidence use as proof that an artifact is scientifically correct;
- infer a missing retrieval or citation record from a use record;
- change the existing SATCOM source register or domain evidence registry;
- fetch anything from a network.

Scientific admission remains governed by the explicit provenance and source
admission records. #9C records only the relationship between those exact artifacts
and downstream contexts.

## Candidate references in Issue #9

Issue #9 names several candidate references for provenance-governance design.
Their appearance in that issue or in repository discussion is not admission.
They must not be represented as `ADMITTED` or used by scientific computation
unless their bibliographic metadata, licence or usage terms, exact bytes,
checksum, applicability, and admission decision are independently verified.

## Relationship to later work

#9D will use the provenance and attribution contracts to link the already-admitted
seventh-arc benchmark fixture and the completed L0.4 validation output without
regenerating either artifact.

#9E will then audit the complete provenance chain and deterministic replay before
Issue #5 aircraft dynamics becomes active.
