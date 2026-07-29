# Evidence Provenance Contract

## Status

This document defines the repository-level provenance foundation implemented by
**Issue #9A**, the checksum/registry layer implemented by **Issue #9B**, and the
bounded attribution/evidence-use layer implemented by **Issue #9C**.

#9A established immutable artifact, source, transformation, lifecycle, and
validation-linkage records. #9B added deterministic exact-byte SHA-256
verification and an immutable local provenance registry. #9C separates evidence
that was retrieved, cited, and actually used by a computation or judgement.

SATCOM migration/linkage and the final Issue #9 audit remain separately gated as
#9D and #9E.

## Purpose

The provenance layer provides one repository-level identity model for scientific
artifacts without replacing the existing domain source registers, SATCOM
provenance artifacts, observation-admission contracts, or evidence-assembly
contracts.

Existing records remain authoritative within their established boundaries. Later
Issue #9 stages adapt and link them into these generic contracts rather than
creating a parallel scientific authority.

## Contract versions

The repository-level provenance record contract is:

```text
PROVENANCE-1
```

The immutable local registry contract is:

```text
PROVENANCE-REGISTRY-1
```

The attribution contract is:

```text
PROVENANCE-ATTRIBUTION-1
```

The implementation is in:

```text
src/mh370_inverse_inference/provenance/models.py
src/mh370_inverse_inference/provenance/checksum.py
src/mh370_inverse_inference/provenance/registry.py
src/mh370_inverse_inference/provenance/attribution.py
```

## Artifact identity

Every governed artifact is represented by an exact `ArtifactReference`
containing:

- `artifact_id` — stable repository identity;
- `version` — explicit artifact version;
- `sha256` — lowercase SHA-256 digest of the exact artifact bytes.

An artifact reference identifies one exact version only. A later version must use
a distinct version value and digest.

## Artifact kinds

The contract defines three artifact kinds:

```text
SOURCE
DERIVED
VALIDATION
```

`SOURCE` represents an exact retrieved or repository-captured source artifact.
`DERIVED` represents an artifact produced deterministically from one or more exact
input artifacts. `VALIDATION` represents a deterministic validation output.

## Admission lifecycle

The contract defines these explicit states:

```text
PROPOSED
VERIFIED
ADMITTED
REJECTED
SUPERSEDED
```

All provenance records are frozen dataclasses. The registry stores the explicit
state carried by each record but does not silently promote, demote, or reinterpret
that state. Scientific admission authority remains with the appropriate governed
review process.

## Source reference

A `SourceReference` records:

- stable source identity;
- publisher;
- title;
- reference URI;
- canonical UTC retrieval timestamp using `Z` notation;
- licence or documented usage terms;
- exact lowercase SHA-256 content hash.

For a `SOURCE` artifact, the artifact SHA-256 must exactly equal the source content
hash, and no transformation history is permitted.

## Transformation history

Each `TransformationStep` records:

- contiguous `step_index`;
- deterministic operation name;
- exact versioned input artifact references;
- exact output artifact reference;
- implementation reference;
- configuration identifier.

`DERIVED` and `VALIDATION` artifacts must contain a transformation history. The
final transformation output must equal the artifact reference governed by the
record.

No hidden normalization, inferred source substitution, nearest-source lookup, or
network retrieval is part of this contract.

## Exact-byte SHA-256 verification

#9B uses the repository's existing deterministic `sha256_bytes` primitive rather
than introducing another hashing algorithm.

`compute_sha256(...)` accepts exact immutable `bytes` only. It does not decode,
normalize line endings, trim whitespace, parse structured content, or rewrite the
payload before hashing.

`verify_sha256(...)` returns an immutable `ChecksumVerification` containing:

- the declared expected SHA-256;
- the SHA-256 computed from the exact supplied bytes;
- a boolean equality result.

`verify_artifact_bytes(...)` and `verify_source_bytes(...)` bind this operation
directly to the digest declared by an `ArtifactReference` or `SourceReference`.
Malformed expected digests fail closed.

## Immutable local provenance registry

`ProvenanceRegistrySnapshot` is an immutable, repository-local index of
`ArtifactProvenanceRecord` values.

The registry is intentionally not a network service, database authority, or
mutable singleton. A snapshot:

- stores only explicit provenance records supplied by the caller;
- canonicalizes records by artifact ID, version, and exact digest;
- rejects duplicate or conflicting `artifact_id` + `version` identities;
- computes a deterministic SHA-256 over the canonical record payload;
- validates its own `snapshot_sha256` on construction;
- requires exact version lookup and never falls back to a nearby or latest
  version implicitly.

`register_record(...)` does not mutate an existing snapshot. It returns a new
canonical snapshot and rejects an already registered artifact ID/version.
Historical snapshots can therefore remain hash-addressable evidence of prior
registry state.

The registry exposes bounded deterministic queries for:

- exact artifact-version lookup;
- exact `ArtifactReference` containment;
- listing all versions of one stable artifact ID;
- listing records by explicit admission state.

## Attribution and evidence-use linkage

#9C introduces three separate immutable record classes rather than one overloaded
provenance flag:

```text
RetrievedEvidenceRecord
CitationRecord
EvidenceUseRecord
```

A `RetrievedEvidenceRecord` states only that one exact artifact was available to
a named context. It does not imply citation, admission, or use.

A `CitationRecord` states that one exact artifact was cited in a named output
context and records a stable citation locator. Citation does not imply admission
or computational use. This permits a candidate or rejected artifact to be cited
when documenting why it was not admitted.

An `EvidenceUseRecord` states that one exact artifact affected a named computation
or judgement. The use kind is explicit:

```text
COMPUTATION
JUDGEMENT
```

Evidence use is fail-closed. The exact artifact reference must exist in the bound
provenance registry snapshot and its admission state must be `ADMITTED`.

`AttributionSnapshot` binds all three collections to one exact
`ProvenanceRegistrySnapshot` by storing its `snapshot_sha256`. The attribution
snapshot:

- verifies every referenced artifact against that exact registry snapshot;
- keeps retrieved, cited, and used evidence separate;
- canonicalizes each collection by stable record ID;
- rejects duplicate IDs across the three attribution record classes;
- hashes its canonical payload deterministically;
- never infers a missing retrieval, citation, or use record from another role.

This distinction makes it possible to audit whether a source was merely available,
was actually cited, or materially affected a computation or judgement.

Additional #9C boundary detail is documented in `docs/references.md`.

## Relationship to the existing evidence registry

The repository already contains `mh370_inverse_inference.evidence.registry`, which
is the L2.4 registry for registered evidence identities and observation lineage.

The repository-level provenance registry does not replace that component. Its
namespace and identity boundary are different:

- the evidence registry indexes registered evidence/observation identities;
- the provenance registry indexes exact scientific artifact versions and their
  provenance records;
- the attribution layer records downstream relationship to exact provenance
  artifacts without merging either registry.

#9D may create explicit adapters between those boundaries, but #9C does not create
hidden cross-registry authority.

## Uncertainty and limitations

`ArtifactProvenanceRecord` carries ordered uncertainty notes and limitations as
explicit immutable fields. These fields preserve scientific caveats alongside
artifact identity rather than leaving them only in narrative documentation.

The checksum, registry, and attribution layers do not interpret, weight, or score
uncertainty.

## Supersession

An artifact in state `SUPERSEDED` must identify a distinct replacement artifact
reference. Other admission states cannot silently carry a supersession target.

Supersession does not delete or rewrite the older artifact identity.

## Validation linkage

`ValidationReportRecord` links:

- stable validation ID and version;
- exact versioned input artifact references;
- exact validation output artifact reference;
- model version;
- configuration ID.

Issue #9D will use this contract together with #9C attribution to link the
already-admitted seventh-arc fixture and the completed L0.4 validation output
without regenerating either artifact.

## Explicit exclusions

This stage does not add:

- automatic filesystem discovery or registry population;
- in-place registry mutation;
- implicit admission based on retrieval or citation;
- automatic source discovery;
- network retrieval;
- source-authority promotion;
- migration of existing SATCOM records;
- BFO processing;
- aircraft dynamics;
- trajectory inference;
- debris modelling;
- probability or ranking;
- endpoint selection;
- search-area recommendation;
- crash-location claims.

## Issue #9 sequence

```text
#9A provenance schemas and immutable contracts      complete
 ↓
#9B checksum verification and local registry        complete
 ↓
#9C attribution and evidence-use linkage            current
 ↓
#9D SATCOM fixture + L0.4 validation provenance linkage
 ↓
#9E full provenance audit and deterministic replay
 ↓
#5 L1 Aircraft Dynamics and Reachability
```

Aircraft dynamics remains blocked until the complete Issue #9 gate is closed.
