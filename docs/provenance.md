# Evidence Provenance Contract

## Status

This document defines the repository-level provenance foundation implemented by
**Issue #9A**, the checksum/registry layer implemented by **Issue #9B**, the
attribution/evidence-use layer implemented by **Issue #9C**, and the exact SATCOM
fixture/validation linkage implemented by **Issue #9D**.

#9E is the current final gate. It adds the fail-closed full provenance audit and
deterministic replay over the exact #9A–#9D chain.

## Purpose

The provenance layer provides one repository-level identity model for scientific
artifacts without replacing the existing domain source registers, SATCOM
provenance artifacts, observation-admission contracts, or evidence-assembly
contracts.

Existing records remain authoritative within their established boundaries. The
Issue #9 stages adapt and link them into generic contracts rather than creating a
parallel scientific authority.

## Contract versions

```text
PROVENANCE-1
PROVENANCE-REGISTRY-1
PROVENANCE-ATTRIBUTION-1
SATCOM-PROVENANCE-LINKAGE-1
PROVENANCE-AUDIT-1
```

The implementation is in:

```text
src/mh370_inverse_inference/provenance/models.py
src/mh370_inverse_inference/provenance/checksum.py
src/mh370_inverse_inference/provenance/registry.py
src/mh370_inverse_inference/provenance/attribution.py
src/mh370_inverse_inference/provenance/satcom_linkage.py
src/mh370_inverse_inference/provenance/audit.py
```

## Artifact identity

Every governed artifact is represented by an exact `ArtifactReference` containing
an artifact ID, explicit version, and lowercase SHA-256 digest. No latest-version,
nearest-source, or inferred-substitution behaviour is permitted.

## Admission lifecycle

```text
PROPOSED
VERIFIED
ADMITTED
REJECTED
SUPERSEDED
```

The registry stores the explicit state supplied by the governed record. It does
not promote or reinterpret scientific authority.

## Exact-byte checksum verification

`compute_sha256(...)` accepts immutable `bytes` and performs no decoding,
normalization, trimming, parsing, or line-ending conversion before hashing.
Malformed or mismatched expected digests fail closed.

## Immutable local registry

`ProvenanceRegistrySnapshot` canonically orders exact artifact records, rejects
conflicting artifact ID/version identities, computes its own deterministic hash,
and requires exact lookup.

## Attribution and evidence use

The attribution contract keeps these roles separate:

```text
RetrievedEvidenceRecord
CitationRecord
EvidenceUseRecord
```

Retrieval does not imply citation or use. Citation does not imply admission or
computational use. Evidence use requires an exact `ADMITTED` artifact in the
bound registry snapshot.

## SATCOM linkage

#9D links the admitted seventh-arc fixture and completed L0.4 validation-output
identity into the generic registry, validation-report, and attribution contracts
without regenerating either artifact.

The fixed identities are:

```text
fixture SHA-256
3ae049f3de7383a433cb8b0b2e1a83e503da99d0dd6e0e96bb9cc39b530cd5a7

validation-output SHA-256
6d4b73fd19afaf3aabec46520551be9d05ab89aa25db11126cad747103452982
```

## Full audit and deterministic replay

#9E audits the exact #9A–#9D identity chain and reconstructs canonical hashes for:

- frozen artifact references;
- artifact provenance records;
- the registry snapshot;
- the validation report;
- retrieved, cited, and used attribution records;
- the attribution snapshot;
- the final linkage payload;
- the final replay digest.

Replay does not rerun scientific source discovery, regenerate the SATCOM fixture,
or create a second copy of the L0.4 validation output. Any broken exact reference,
state, transformation, validation link, snapshot binding, or replay step produces
failure.

See `docs/provenance-audit-and-replay.md` for the complete #9E boundary.

## Relationship to existing authorities

The repository-level provenance registry does not replace
`mh370_inverse_inference.evidence.registry`, the SATCOM source registers, final
admission review, transform records, fixture sampling contract, or Issue #7
validation implementation. It links exact identities across those boundaries.

## Explicit exclusions

Issue #9 introduces no BFO inversion, aircraft dynamics, trajectory generation,
debris modelling, probability or ranking, endpoint selection, search-area
recommendation, or crash-location claim.

## Issue #9 sequence

```text
#9A provenance schemas and immutable contracts      complete
 ↓
#9B checksum verification and local registry        complete
 ↓
#9C attribution and evidence-use linkage            complete
 ↓
#9D SATCOM fixture + L0.4 validation linkage        complete
 ↓
#9E full provenance audit and deterministic replay  current
 ↓
#5 L1 Aircraft Dynamics and Reachability
```

Aircraft dynamics remains blocked until #9E passes, is merged, and Issue #9 is
formally closed.
